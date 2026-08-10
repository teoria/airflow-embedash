# Airflow + Grafana monitoring

A runnable local environment that puts a Grafana dashboard of Airflow pipeline
health **inside the Airflow UI**, using the Embedash package from this repository.

Everything here is a demo and reference setup: two Docker Compose stacks (one
for Airflow 2, one for Airflow 3), a small DAG that generates run history, a
provisioned Grafana instance, and the SQL behind the dashboard panels.

The reference Grafana dashboard was authored by Diego Lopes.

## What you get

| Service | URL | Notes |
| --- | --- | --- |
| Airflow | http://localhost:8080 | Grafana appears in the Airflow nav |
| Grafana | http://localhost:3000 | Anonymous viewer, embedding allowed |
| PostgreSQL | internal | Airflow metadata DB, also Grafana's datasource |

Two dashboards are provisioned into a Grafana folder named `Airflow`:

- `airflow-embedash-demo` — Airflow observability overview
- `airflow-dag-runtime` — Airflow DAG runtime details

## Requirements

- Docker with Compose v2
- GNU Make
- Ports 8080 and 3000 free

## Quick start

```bash
make build        # build the Airflow image with the plugin installed
make up           # start Airflow, PostgreSQL and Grafana
make wait         # block until the Airflow API reports healthy
make unpause-dag  # the demo DAG is paused on creation; unpause it for data
make open         # print the UI URLs
```

The demo DAG runs every two minutes. Give it a few minutes before the dashboard
panels have something to show, or force a run now with `make trigger-dag`.

The init container automatically adds both provisioned Grafana dashboards to
Embedash. Open **Dashboards** in the Airflow navigation and select either:

| Name | URL |
| --- | --- |
| Airflow pipeline health | `http://localhost:3000/d/airflow-embedash-demo/airflow-pipeline-health?orgId=1&kiosk` |
| Airflow DAG runtime | `http://localhost:3000/d/airflow-dag-runtime/airflow-dag-runtime?orgId=1&kiosk` |

The seeded entries have an empty **Payload**, so Embedash embeds the public
Grafana URLs as-is. The seed only runs when the `embeded_dashboards` Airflow
Variable does not already exist; it will never overwrite dashboards you add or
edit locally.

Tear down with `make down`, or `make clean` to also drop the volumes.

## Choosing the Airflow version

`VERSION` in the `Makefile` selects the stack. It defaults to `3`.

```bash
make up              # Airflow 3
make VERSION=2 up    # Airflow 2
```

Each version has its own Compose file and Dockerfile under
`dev/airflow/v2/` and `dev/airflow/v3/`. The Makefile derives the UI service
name and health endpoint from `VERSION`, so every target follows the switch.

The two stacks differ in ways worth knowing:

| | Airflow 2 (2.9.1) | Airflow 3 (3.3.0) |
| --- | --- | --- |
| UI service | `airflow-webserver` | `airflow-api-server` |
| Health endpoint | `/health` | `/api/v2/monitor/health` |
| DAG parsing | scheduler | separate `airflow-dag-processor` |
| Login | `admin` / `admin` | none (all-admins simple auth) |
| Plugin mechanism | Flask-AppBuilder view | Airflow External View |
| Dashboard config | Embedash CRUD screen in the UI | Embedash CRUD screen in the UI |

Airflow 2 has no simple auth manager, so its init container seeds a fixed
`admin` / `admin` account. Both stacks are local-only and deliberately
unauthenticated or trivially authenticated — do not copy these settings into a
deployed environment. This includes the fixed Fernet key used only to let every
demo container decrypt the same seeded Airflow Variables.

### Embedash source

Both demo images install the package from this checkout, which supports Airflow 2.x
and Airflow 3.1+. Rebuild the image after changing Embedash:

```bash
make build
```

## Configuring dashboards

The two demo dashboards are seeded during initialization. To add another
dashboard, use the Embedash **Dashboards** entry in the Airflow navigation,
select **Add New Dashboard**, and leave **Payload** empty for Grafana URLs.
This is the same workflow on Airflow 2 and Airflow 3.

The URL is loaded by the browser, not by Airflow, so it must be reachable from
the browser and Grafana must permit framing by the Airflow origin. Never put a
Grafana API key in the URL. Handle Grafana access in Grafana (OAuth, auth
proxy, or a scoped anonymous viewer).

## Repository layout

```
dev/airflow/v2/          Airflow 2 Compose stack and Dockerfile
dev/airflow/v3/          Airflow 3 Compose stack and Dockerfile
dev/dags/                embedash_demo.py — extract/transform/load, every 2 min
dev/grafana/provisioning Grafana datasource and dashboard provisioning
grafana/                 airflow3_monitoring.sql — the panel queries
docs/                    airflow3-grafana.md — production integration notes
Makefile                 all local workflow commands
```

Both Dockerfiles build from the repository root so the Compose files can be
kept beside their stack.

## Make targets

| Target | What it does |
| --- | --- |
| `help` | List targets (default target) |
| `build` | Build the Airflow image for the selected version |
| `up` / `down` / `restart` | Manage the stack |
| `status` / `logs` | Container state and streaming logs |
| `wait` | Poll the Airflow health endpoint until ready |
| `setup` | `up`, `install`, then `wait` |
| `install` | Prints a note; the plugin is baked into the image at build time |
| `open` | Print the Airflow and Grafana URLs |
| `clean` | `down -v`, removing volumes |
| `shell` | Bash in the Airflow UI container |
| `dags` | List DAGs |
| `unpause-dag` | Unpause `embedash_demo` |
| `trigger-dag` | Trigger `embedash_demo` now |
| `list-tasks` / `dag-info` | Inspect `embedash_demo` |
| `plugin-info` | List loaded Airflow plugins |
| `airflow-help` | Airflow CLI help |
| `test` | Run pytest inside the container |

`make test` runs tests bundled with the installed Embedash package, when
available. The main verification for this repository is starting the selected
Compose stack and adding a provisioned Grafana dashboard through the UI.

## The Grafana queries

[`grafana/airflow3_monitoring.sql`](grafana/airflow3_monitoring.sql) holds the
panel queries, written against the Airflow 3.x metadata model. They join on
`(dag_id, run_id)`, use `logical_date` for display only, and read DAGs from
`dag_run`.

Airflow treats its metadata schema as an internal detail. Keep this SQL in
version control and revalidate it after every Airflow upgrade; prefer the REST
API for anything needing a stable contract.

In this demo Grafana connects as the `airflow` database user for convenience.
For any real deployment, create a dedicated read-only role instead — see
[`docs/airflow3-grafana.md`](docs/airflow3-grafana.md) for the grants and the
rest of the production setup.

## Troubleshooting

**No Embedash entry in the Airflow nav.** Run `make plugin-info` and confirm
that the image was rebuilt after your Embedash changes.

**Dashboard panels are empty.** The demo DAG is paused on creation. Run
`make unpause-dag`, then `make trigger-dag`, and confirm with `make dags`.

**Grafana shows no dashboards.** Check the provisioning mount resolved:
`make logs` and look for the `grafana` service reading
`/etc/grafana/provisioning`.

**DAG import errors.** `make shell`, then `airflow dags list-import-errors`.
The demo DAG imports from `airflow.decorators`, which works on both Airflow 2
and 3.

## License

This example is distributed under the repository's MIT License.
