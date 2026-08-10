"""Small scheduled DAG that gives the local Grafana dashboard real data."""

from __future__ import annotations

import time

import pendulum
from airflow.decorators import dag, task  # works on both Airflow 2 and 3


@dag(
    dag_id="embedash_demo",
    description="Demo pipeline for the airflow-embedash Grafana dashboard",
    schedule="*/2 * * * *",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    tags=["embedash", "demo"],
)
def embedash_demo():
    @task
    def extract() -> None:
        time.sleep(3)

    @task
    def transform() -> None:
        time.sleep(6)

    @task
    def load() -> None:
        time.sleep(2)

    extract() >> transform() >> load()


embedash_demo()

