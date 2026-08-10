"""Seed the demo Embedash dashboards once, without overwriting user changes."""

from __future__ import annotations

from airflow.models import Variable


DASHBOARDS_VARIABLE = "embeded_dashboards"
DASHBOARDS = [
    {
        "id": "airflow-pipeline-health",
        "name": "Airflow pipeline health",
        "description": "Airflow pipeline status and latest-run overview",
        "url": (
            "http://localhost:3000/d/airflow-embedash-demo/"
            "airflow-pipeline-health?orgId=1&kiosk"
        ),
        "type": "public",
        "payload": {},
    },
    {
        "id": "airflow-dag-runtime",
        "name": "Airflow DAG runtime",
        "description": "Runtime history and summary by DAG",
        "url": "http://localhost:3000/d/airflow-dag-runtime/airflow-dag-runtime?orgId=1&kiosk",
        "type": "public",
        "payload": {},
    },
]


if Variable.get(DASHBOARDS_VARIABLE, default_var=None) is None:
    Variable.set(DASHBOARDS_VARIABLE, DASHBOARDS, serialize_json=True)
    print("Seeded Embedash Grafana dashboards.")
else:
    print("Embedash dashboards already exist; leaving them unchanged.")
