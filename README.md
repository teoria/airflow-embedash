# Airflow Embedash

Embed dashboards in the Apache Airflow UI. Point it at a Metabase, Grafana or Datadog URL and the
dashboard shows up as a page inside Airflow, next to your DAGs.

Dashboards are managed from a settings page in the UI — no code changes, no redeploy.

## Compatibility

| Airflow | Supported | How it renders |
|---------|-----------|----------------|
| 2.x | Yes | Flask-AppBuilder views (`plugin/airflow2.py`) |
| 3.0 | No | Plugin FastAPI apps and external views do not exist before 3.1 |
| 3.1+ | Yes | FastAPI app plus one external view (`plugin/airflow3.py`) |

`plugin/__init__.py` picks the layer from the running Airflow version, so the same package works on
both. The HTML templates are shared.

## Installation

```bash
pip install airflow-embedash
```

The plugin registers itself through the `airflow.plugins` entry point — nothing to copy into your
`plugins/` folder. Restart the API server (Airflow 3) or webserver (Airflow 2) afterwards.

> Installing by copying the package into `plugins/` is not supported. Airflow scans that folder file
> by file, which imports both version layers directly and fails on whichever one does not match your
> Airflow version.

## Configuration

All settings are **Airflow Variables**, not environment variables.

| Variable | Description | Required |
|----------|-------------|----------|
| `embeded_dashboards` | The dashboard list. Managed for you by the settings page — you should not need to edit it by hand. | Created on first save |
| `embeded_dashboards_metabase_token` | Metabase secret key, used to sign embed URLs for private dashboards. | Only for private dashboards |
| `embeded_dashboards_menu_label` | Label for the nav entry. Defaults to `Dashboards`. | Optional |

Changing `embeded_dashboards_menu_label` needs an API server restart, because Airflow reads plugin
nav entries once at load.

## Usage

### Adding a dashboard

Open the nav entry, then **Add New Dashboard**. Four fields:

- **Dashboard Name** — shown in the list.
- **Description** — free text.
- **URL** — for a public dashboard, the URL to embed as-is. For a private Metabase dashboard, your
  Metabase site URL (for example `https://metabase.example.com`).
- **Payload** — leave empty for a public dashboard. Fill it in to make the dashboard private.

### Public vs private

**Public** (empty payload): the URL is embedded in an iframe unchanged. Works with any dashboard tool
that allows framing — Grafana, Datadog, a public Metabase link.

**Private** (payload set): Metabase signed embedding. The payload is the Metabase resource claim, for
example:

```json
{"resource": {"dashboard": 1}, "params": {}}
```

On each view the plugin adds a 10-minute `exp`, signs the payload with
`embeded_dashboards_metabase_token` (HS256), and frames
`<url>/embed/dashboard/<token>#bordered=true&titled=true`. The token is minted per request, so it is
never stored in the Variable and expires quickly.

### URLs (Airflow 3)

Every page has its own address, so dashboards can be bookmarked and shared:

| URL | Page |
|-----|------|
| `/plugin/embedash` | Dashboard list |
| `/plugin/embedash/add` | Add form |
| `/plugin/embedash/edit/<id>` | Edit form |
| `/plugin/embedash/view/<id>` | An embedded dashboard |

Airflow frames plugin pages, so the address bar belongs to the Airflow UI rather than to the framed
page. The plugin keeps the two in step: each page writes its own URL into the address bar, and
follows it when Airflow changes it (clicking the nav entry while a dashboard is open returns you to
the list). See `embedashSyncUrl` in `plugin/templates/af3_base.html`.

New dashboards appear in the list immediately. On Airflow 2 the menu is built at plugin load, so a
restart is needed there before a new dashboard shows up in the menu.

### Permissions

Airflow does not authenticate plugin endpoints, so this plugin does it explicitly:

- **Airflow 3.1+** — every page requires a logged-in user. Adding, editing and deleting additionally
  require Variable edit access, since that is where dashboards are stored.
- **Airflow 2** — read access on the website resource.

## Package structure

```
airflow_embedash/
└── plugin/
    ├── __init__.py           # Entry point; selects the layer by Airflow version
    ├── airflow2.py           # Airflow 2 layer (Flask-AppBuilder)
    ├── airflow3.py           # Airflow 3.1+ layer (FastAPI + external view)
    └── templates/            # Shared by both layers
        ├── af3_base.html         # Standalone page shell for Airflow 3, plus URL syncing
        ├── index.html            # Airflow 3 entry page; forwards to the page in the URL
        ├── settings.html         # Dashboard list
        ├── add_dashboard.html
        ├── edit_dashboard.html
        ├── view.html             # The iframe that holds a dashboard
        └── view_not_set_up.html
tests/
└── test_airflow3_plugin.py   # End-to-end check against a running Airflow 3
dev/                          # Local Airflow 3 environment (Docker Compose)
```

## Development

Start a local Airflow 3.1 with the plugin installed:

```bash
make up          # docker compose -f dev/docker-compose.yaml up -d
make logs
make down
```

The UI is at http://localhost:8080 (`airflow` / `airflow`). `dev/docker-compose.yaml` mounts
`airflow_embedash/` over its editable install in the container, so local edits are live:

- **Template changes** are picked up on the next page load.
- **Python changes** need a restart: `docker restart dev-airflow-apiserver-1`.

To exercise the Airflow 2 layer instead, use the other compose file. Both bind host port 8080, so
stop one before starting the other:

```bash
docker compose -f dev/docker-compose.yaml stop            # Airflow 3, project "dev"
docker compose -f dev/docker-compose_v2.yaml up -d --build # Airflow 2.11, project "embedash-af2"
```

They are separate Compose projects on purpose — sharing a project name makes the services they have
in common reuse each other's images, and an Airflow 2 service will happily start from the Airflow 3
image and fail in confusing ways. Log in with `admin` / `admin` there.

Check the plugin loaded under **Admin → Plugins**, or:

```bash
curl -s localhost:8080/api/v2/plugins/importErrors   # with an auth token
```

### Tests

`tests/test_airflow3_plugin.py` walks the whole flow against a running instance — authentication,
create, private view, edit, invalid payload, delete — using only the standard library:

```bash
python tests/test_airflow3_plugin.py

AIRFLOW_URL=http://localhost:8080 AIRFLOW_USER=airflow AIRFLOW_PASSWORD=airflow \
  python tests/test_airflow3_plugin.py
```

It creates a dashboard named `embedash-e2e` and deletes it again. It never writes
`embeded_dashboards_metabase_token`; if that Variable already exists, the signed-URL path is checked
too, otherwise that assertion is skipped.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes, with a test where there is logic to break
4. Confirm `python tests/test_airflow3_plugin.py` passes against a local Airflow
5. Open a pull request

## License

This project is licensed under the MIT License.
