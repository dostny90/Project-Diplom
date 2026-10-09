"""Persistence helpers for CIC network flows and ML predictions."""

from __future__ import annotations

import math
import os
from datetime import datetime
from numbers import Real
from pathlib import Path
from typing import Any


def _db_url() -> str:
    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError("Set DATABASE_URL to the PostgreSQL connection string.")
    return value


def _first(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None


def _integer(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        result = int(float(value))
    except (TypeError, ValueError, OverflowError):
        return None
    return result


def _timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def _numeric_features(row: dict[str, Any]) -> dict[str, int | float]:
    # train.py drops identifiers, IP addresses, timestamps, and Label before
    # fitting. Keep the remaining numeric values in a shape suitable for JSONB.
    excluded = {
        "Label", "Timestamp", "Flow ID", "Source IP", "Src IP",
        "Destination IP", "Dst IP",
    }
    features: dict[str, int | float] = {}
    for key, value in row.items():
        if key.strip() in excluded or isinstance(value, bool) or not isinstance(value, Real):
            continue
        number = float(value)
        if math.isfinite(number):
            features[key.strip()] = int(number) if number.is_integer() else number
    return features


def initialize_database() -> None:
    """Create the tables and indexes in data/schema.sql if they do not exist."""
    import psycopg

    schema_path = Path(__file__).with_name("schema.sql")
    with psycopg.connect(_db_url()) as connection:
        connection.execute(schema_path.read_text(encoding="utf-8"))


def save_prediction(
    input_data: dict[str, Any],
    prediction: dict[str, Any],
    model_name: str = "RandomForestClassifier",
) -> tuple[int, int]:
    """Store one traffic flow and its detector.predict() result; return their IDs."""
    from psycopg import connect
    from psycopg.types.json import Jsonb

    status = prediction.get("status")
    is_anomaly = prediction.get("is_anomaly")
    confidence = prediction.get("confidence")
    if status not in {"Normal", "Anomaly"} or not isinstance(is_anomaly, bool):
        raise ValueError("prediction must contain status and boolean is_anomaly")
    if (status == "Anomaly") != is_anomaly:
        raise ValueError("status and is_anomaly do not agree")
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        raise ValueError("prediction.confidence must be a number from 0 to 100") from None
    if not math.isfinite(confidence) or not 0 <= confidence <= 100:
        raise ValueError("prediction.confidence must be a number from 0 to 100")

    flow_key = _first(input_data, "Flow ID", "flow_id", "flow_key")
    source_ip = _first(input_data, "Source IP", "Src IP", "src_ip", "source_ip")
    source_port = _integer(_first(input_data, "Src Port", "Source Port", "src_port", "source_port"))
    destination_ip = _first(input_data, "Destination IP", "Dst IP", "dst_ip", "destination_ip")
    destination_port = _integer(_first(input_data, "Dst Port", "Destination Port", "dst_port", "destination_port"))
    protocol = _integer(input_data.get("Protocol", input_data.get("protocol")))
    observed_at = _timestamp(_first(input_data, "Timestamp", "timestamp", "observed_at"))
    raw_label = _first(input_data, "Label", "label")
    features = _numeric_features(input_data)

    with connect(_db_url()) as connection:
        flow_id = connection.execute(
            """INSERT INTO network_flows
               (flow_key, observed_at, source_ip, source_port, destination_ip,
                destination_port, protocol, features, raw_label)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (flow_key, observed_at, source_ip, source_port, destination_ip,
             destination_port, protocol, Jsonb(features), raw_label),
        ).fetchone()[0]
        prediction_id = connection.execute(
            """INSERT INTO anomaly_predictions
               (flow_id, model_name, status, is_anomaly, confidence)
               VALUES (%s, %s, %s, %s, %s)
               RETURNING id""",
            (flow_id, model_name, status, is_anomaly, confidence),
        ).fetchone()[0]
    return flow_id, prediction_id


def predict_and_save(
    input_data: dict[str, Any], detector: Any,
    model_name: str = "RandomForestClassifier",
) -> dict[str, Any]:
    """Run AnomalyDetector.predict(), persist both records, and return the result."""
    result = detector.predict(input_data)
    flow_id, prediction_id = save_prediction(input_data, result, model_name)
    return {**result, "flow_id": flow_id, "prediction_id": prediction_id}
