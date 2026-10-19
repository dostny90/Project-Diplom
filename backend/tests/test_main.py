import psycopg
import pytest
from fastapi.testclient import TestClient

from backend import main

SAMPLE_FLOW = {"Dst Port": 21, "Protocol": 6, "Flow Duration": 1000, "Tot Fwd Pkts": 5}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    # Контекстный менеджер запускает lifespan, то есть загружает настоящую модель
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture
def with_database(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://test@localhost/test")


def test_health_without_database(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model_loaded": True, "database": "disabled"}


def test_health_reports_unavailable_database(client, with_database, monkeypatch):
    monkeypatch.setattr(main.database, "ping", lambda: False)
    assert client.get("/health").json()["database"] == "unavailable"


def test_predict_without_database(client):
    response = client.post("/predict", json=SAMPLE_FLOW)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"Normal", "Anomaly"}
    assert body["is_anomaly"] == (body["status"] == "Anomaly")
    assert 0 <= body["confidence"] <= 100
    assert body["saved"] is False


def test_predict_saves_to_database(client, with_database, monkeypatch):
    saved = {}

    def fake_predict_and_save(flow, detector):
        saved["flow"] = flow
        return {**detector.predict(flow), "flow_id": 7, "prediction_id": 11}

    monkeypatch.setattr(main.database, "predict_and_save", fake_predict_and_save)
    body = client.post("/predict", json=SAMPLE_FLOW).json()
    assert saved["flow"] == SAMPLE_FLOW
    assert body["flow_id"] == 7
    assert body["prediction_id"] == 11
    assert body["saved"] is True


def test_predict_returns_503_when_database_fails(client, with_database, monkeypatch):
    def broken(flow, detector):
        raise psycopg.OperationalError("connection refused")

    monkeypatch.setattr(main.database, "predict_and_save", broken)
    assert client.post("/predict", json=SAMPLE_FLOW).status_code == 503


def test_predict_rejects_empty_flow(client):
    assert client.post("/predict", json={}).status_code == 422


def test_predict_rejects_non_numeric_feature(client):
    response = client.post("/predict", json={"Dst Port": "не число"})
    assert response.status_code == 422


def test_anomalies_require_database(client):
    assert client.get("/anomalies").status_code == 503


def test_anomalies_returns_rows(client, with_database, monkeypatch):
    rows = [{"prediction_id": 1, "flow_id": 1, "confidence": 97.5}]
    requested = {}

    def fake_list(limit):
        requested["limit"] = limit
        return rows

    monkeypatch.setattr(main.database, "list_anomalies", fake_list)
    response = client.get("/anomalies", params={"limit": 10})
    assert response.status_code == 200
    assert response.json() == rows
    assert requested["limit"] == 10


def test_anomalies_limit_is_validated(client, with_database):
    assert client.get("/anomalies", params={"limit": 0}).status_code == 422
