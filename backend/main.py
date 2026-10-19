"""FastAPI-сервис детекции аномалий сетевого трафика.

Запуск из корня проекта:
    uvicorn backend.main:app --reload
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import psycopg
from fastapi import Body, FastAPI, HTTPException, Query, Request

from data import database
from ml_model.predict import AnomalyDetector

MODEL_DIR = Path(__file__).resolve().parents[1] / "ml_model"

SAMPLE_FLOW = {
    "Dst Port": 21,
    "Protocol": 6,
    "Flow Duration": 1000,
    "Tot Fwd Pkts": 5,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Модель загружается один раз при старте, а не на каждый запрос
    app.state.detector = AnomalyDetector(
        model_path=MODEL_DIR / "model.pkl",
        features_path=MODEL_DIR / "features.pkl",
    )
    yield


app = FastAPI(
    title="Детекция аномалий сетевого трафика",
    description="Классификация сетевых потоков (CIC) моделью Random Forest "
                "и хранение результатов в PostgreSQL.",
    lifespan=lifespan,
)


def _database_enabled() -> bool:
    # Без DATABASE_URL сервис работает, но предсказания не сохраняются
    return bool(os.getenv("DATABASE_URL"))


@app.get("/health")
def health(request: Request) -> dict[str, Any]:
    """Состояние сервиса: загружена ли модель и доступна ли база."""
    if not _database_enabled():
        db_status = "disabled"
    else:
        db_status = "ok" if database.ping() else "unavailable"
    return {
        "status": "ok",
        "model_loaded": hasattr(request.app.state, "detector"),
        "database": db_status,
    }


@app.post("/predict")
def predict(
    request: Request,
    flow: dict[str, Any] = Body(..., examples=[SAMPLE_FLOW]),
) -> dict[str, Any]:
    """Классифицирует один сетевой поток.

    Тело запроса — словарь признаков потока с названиями столбцов CIC
    (например, "Dst Port", "Flow Duration"). Отсутствующие признаки
    считаются нулями.
    """
    if not flow:
        raise HTTPException(422, "Передайте хотя бы один признак потока")
    detector = request.app.state.detector
    try:
        if not _database_enabled():
            return {**detector.predict(flow), "saved": False}
        return {**database.predict_and_save(flow, detector), "saved": True}
    except ValueError as exc:
        raise HTTPException(422, f"Некорректные значения признаков: {exc}") from exc
    except psycopg.Error as exc:
        raise HTTPException(503, "База данных недоступна") from exc


@app.get("/anomalies")
def anomalies(limit: int = Query(50, ge=1, le=500)) -> list[dict[str, Any]]:
    """Последние обнаруженные аномалии, новые первыми."""
    if not _database_enabled():
        raise HTTPException(503, "База данных не настроена: задайте DATABASE_URL")
    try:
        return database.list_anomalies(limit)
    except psycopg.Error as exc:
        raise HTTPException(503, "База данных недоступна") from exc
