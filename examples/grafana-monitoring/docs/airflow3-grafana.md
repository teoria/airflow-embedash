# Grafana monitoring with Airflow 3

Airflow Embedash v0.3.2 supports Airflow 3.1+ and renders Grafana as an
External View inside the Airflow UI. Grafana dashboards are configured through
the Embedash CRUD screen, not an environment variable.

The reference Grafana dashboard shipped with this demo was authored by Diego
Lopes and is intended as an example observability dashboard for Airflow.

For a runnable local version of everything below, see the
[README](../README.md).

## 1. Install and configure the plugin

Install the package in the image used by the Airflow API server:

```bash
pip install 'airflow-embedash==0.3.2'
```

Restart the Airflow API server after installation. Airflow 3.0 is not
supported; use Airflow 3.1 or newer.

Open **Dashboards** in the Airflow navigation and select **Add New Dashboard**.
Set a name and description, then use the Grafana dashboard URL, for example:

```text
https://grafana.example.com/d/airflow-pipelines/airflow-pipeline-health?orgId=1&kiosk
```

Leave **Payload** empty: it is only for private Metabase signed embeds. Save
the dashboard. Embedash stores its configuration in an Airflow Variable and
the dashboard is immediately available in the dashboard list.

The Grafana URL must be reachable from the user's browser and Grafana must
allow framing by the Airflow origin. Configure Grafana authentication there
(for example OAuth, auth proxy, or a scoped anonymous viewer); never put a
Grafana API key in the URL.

## 2. Give Grafana read-only access

Create a dedicated PostgreSQL login for the Airflow metadata database. The
exact database and schema names differ by deployment; this is an example:

```sql
CREATE ROLE grafana_airflow LOGIN PASSWORD 'use-a-secret-manager';
GRANT CONNECT ON DATABASE airflow TO grafana_airflow;
GRANT USAGE ON SCHEMA public TO grafana_airflow;
GRANT SELECT ON TABLE public.dag_run, public.task_instance TO grafana_airflow;
```

Do not grant write permissions and do not use the Airflow application account.
Add this connection as a PostgreSQL datasource in Grafana and import the panel
queries from [`grafana/airflow3_monitoring.sql`](../grafana/airflow3_monitoring.sql).

## What changed from the 2020 queries

The old queries identify a task instance by `(dag_id, execution_date)`, derive
dates from the text of `run_id`, and select DAGs from `public.dag`. In current
Airflow, `execution_date` is legacy terminology for `logical_date`, it is not
guaranteed to be unique, and a manually triggered run need not have a data
interval derived from it. The supplied queries use `(dag_id, run_id)` for every
join, `logical_date` only for display, and `dag_run` to populate the DAG list.

Airflow describes its metadata schema as an internal detail. Treat the SQL as a
versioned operational integration: validate it after each Airflow upgrade and
prefer the public REST API for applications that need a stable contract.

