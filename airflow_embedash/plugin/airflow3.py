"""Airflow 3.1+ version of the Embedash plugin (FastAPI + external views).

The Airflow 2 plugin (``airflow2.py``) uses Flask-AppBuilder, which no longer
exists in Airflow 3. Routes here mirror the AF2 ones so the Jinja templates in
``templates/`` are shared between both.
"""

from __future__ import annotations

import json
import os.path as op
import time
import uuid
from typing import Any
from urllib.parse import urlsplit

import airflow
from airflow.api_fastapi.core_api.security import requires_access_variable, requires_authenticated
from airflow.configuration import conf
from airflow.models import Variable
from airflow.plugins_manager import AirflowPlugin
from fastapi import Depends, FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from packaging.version import Version

AIRFLOW_VERSION = Version(airflow.__version__)
MIN_AIRFLOW_VERSION = Version("3.1.0")

URL_PREFIX = "/embedash"
# Nav icons are <img> sources resolved against the browser origin, not against the
# Airflow UI, so they need the API server's own path prefix (empty unless Airflow is
# served under a sub-path).
API_BASE_PATH = urlsplit(conf.get("api", "base_url", fallback="")).path.rstrip("/")
DASHBOARDS_VAR = "embeded_dashboards"
MENU_LABEL_VAR = "embeded_dashboards_menu_label"
METABASE_TOKEN_VAR = "embeded_dashboards_metabase_token"

# Feather-style "monitor" glyph, drawn to match the stroke icons Airflow uses in the
# nav. The Airflow UI renders external view icons as <img>, so the stroke colour cannot
# be inherited -- one variant is served per colour mode via ``icon_dark_mode``.
DESKTOP_ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>'
    '<line x1="8" y1="21" x2="16" y2="21"/>'
    '<line x1="12" y1="17" x2="12" y2="21"/>'
    "</svg>"
)

templates = Jinja2Templates(directory=op.join(op.dirname(__file__), "templates"))
# The shared templates extend ``base_template`` and reference ``appbuilder`` -- in
# Airflow 2 both come from Flask-AppBuilder, here we supply our own.
templates.env.globals["base_template"] = "af3_base.html"
templates.env.globals["appbuilder"] = {"app_name": "Airflow"}


def ensure_airflow_version_supported() -> None:
    if AIRFLOW_VERSION < MIN_AIRFLOW_VERSION:
        raise RuntimeError(
            f"Embedash AF3 plugin requires Airflow >= {MIN_AIRFLOW_VERSION}; external views and FastAPI "
            f"apps are unavailable on {AIRFLOW_VERSION}."
        )


def get_dashboards() -> list[dict[str, Any]]:
    return Variable.get(DASHBOARDS_VAR, default_var=[], deserialize_json=True)


def set_dashboards(dashboards: list[dict[str, Any]]) -> None:
    Variable.set(key=DASHBOARDS_VAR, value=dashboards, serialize_json=True)


def find_dashboard(id: str) -> dict[str, Any] | None:
    return next((d for d in get_dashboards() if d.get("id") == id), None)


def build_dashboard(id: str, name: str, description: str, url: str, payload: str) -> dict[str, Any]:
    try:
        parsed = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Payload is not valid JSON: {exc}")
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="Payload must be a JSON object.")
    return {
        "id": id,
        "name": name,
        "description": description,
        "url": url,
        "type": "public" if not parsed else "private",
        "payload": parsed,
    }


def signed_metabase_url(dashboard: dict[str, Any]) -> str:
    """Sign the payload of a private dashboard into a Metabase embed URL."""
    import jwt

    payload = dict(dashboard.get("payload") or {})
    payload["exp"] = round(time.time()) + (60 * 10)  # 10 minute expiration
    token = jwt.encode(payload, Variable.get(METABASE_TOKEN_VAR), algorithm="HS256")
    return f"{dashboard.get('url', '')}/embed/dashboard/{token}#bordered=true&titled=true"


def _settings_url(request: Request) -> str:
    # root_path carries the mount prefix (and any reverse-proxy prefix) for this sub-app.
    return f"{request.scope.get('root_path', '')}/settings"


def create_embedash_fastapi_app() -> FastAPI:
    ensure_airflow_version_supported()
    # Plugin endpoints are not authenticated by Airflow -- every route requires a
    # logged-in user, and the ones writing the Variable require Variable edit access.
    app = FastAPI(dependencies=[Depends(requires_authenticated())])
    writes = [Depends(requires_access_variable("PUT"))]

    @app.get("/")
    def index(request: Request) -> Any:
        # Forwards to whichever page the parent URL names -- see index.html.
        return templates.TemplateResponse(request, "index.html", {})

    @app.get("/icon.svg")
    def icon(dark: bool = False) -> Response:
        return Response(
            DESKTOP_ICON_SVG.format(color="#e2e8f0" if dark else "#1a202c"),
            media_type="image/svg+xml",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    @app.get("/settings")
    def settings(request: Request) -> Any:
        return templates.TemplateResponse(request, "settings.html", {"dashboards": get_dashboards()})

    @app.get("/adddashboard")
    def add_dashboard_form(request: Request) -> Any:
        return templates.TemplateResponse(request, "add_dashboard.html", {})

    @app.post("/add_dash", dependencies=writes)
    def add_dashboard(
        request: Request,
        name: str = Form(...),
        description: str = Form(""),
        url: str = Form(...),
        payload: str = Form(""),
    ) -> Any:
        dashboards = get_dashboards()
        dashboards.append(build_dashboard(uuid.uuid4().hex, name, description, url, payload))
        set_dashboards(dashboards)
        return RedirectResponse(_settings_url(request), status_code=303)

    @app.get("/editdashboard/{id}")
    def edit_dashboard_form(request: Request, id: str) -> Any:
        dashboard = find_dashboard(id)
        if dashboard is None:
            # A stale /edit/<id> link, now that these are shareable: an empty form would
            # only post back to a 404.
            return RedirectResponse(_settings_url(request), status_code=303)
        return templates.TemplateResponse(request, "edit_dashboard.html", {"dashboard": dashboard})

    @app.post("/edit_dash/{id}", dependencies=writes)
    def edit_dashboard(
        request: Request,
        id: str,
        name: str = Form(...),
        description: str = Form(""),
        url: str = Form(...),
        payload: str = Form(""),
    ) -> Any:
        updated = build_dashboard(id, name, description, url, payload)
        dashboards = get_dashboards()
        for i, dashboard in enumerate(dashboards):
            if dashboard.get("id") == id:
                dashboards[i] = updated
                break
        else:
            raise HTTPException(status_code=404, detail=f"No dashboard with id {id}")
        set_dashboards(dashboards)
        return RedirectResponse(_settings_url(request), status_code=303)

    @app.get("/deletedashboard/{id}", dependencies=writes)
    def delete_dashboard(request: Request, id: str) -> Any:
        set_dashboards([d for d in get_dashboards() if d.get("id") != id])
        return RedirectResponse(_settings_url(request), status_code=303)

    @app.get("/view/{id}")
    def view_dashboard(request: Request, id: str) -> Any:
        dashboard = find_dashboard(id)
        if dashboard is None:
            return templates.TemplateResponse(request, "view_not_set_up.html", {})
        if dashboard.get("type") == "private" and dashboard.get("payload"):
            dashboard = {**dashboard, "url": signed_metabase_url(dashboard)}
        # 32px = the top/bottom body padding of af3_base.html; there is no Airflow
        # header/footer inside the plugin iframe to offset.
        return templates.TemplateResponse(
            request, "view.html", {"dashboard": dashboard, "height_offset": 32}
        )

    return app


def build_external_views() -> list[dict[str, Any]]:
    """A single nav entry, deliberately.

    Airflow hides plugin nav items behind its own hardcoded "Plugins" plug button as
    soon as two or more of them exist (``PluginMenus.tsx``), which buries both the icon
    and the label. With exactly one item it renders top-level with the icon and name
    below it, so individual dashboards are linked from the settings page instead of
    getting a nav entry each.
    """
    return [
        {
            "name": Variable.get(MENU_LABEL_VAR, default_var="Embedash"),
            # The index page, not /settings: it forwards to whichever dashboard the
            # parent URL names, so a linked dashboard survives a reload.
            "href": f"{URL_PREFIX.lstrip('/')}/",
            "url_route": URL_PREFIX.lstrip("/"),
            "destination": "nav",
            "icon": f"{API_BASE_PATH}{URL_PREFIX}/icon.svg",
            "icon_dark_mode": f"{API_BASE_PATH}{URL_PREFIX}/icon.svg?dark=true",
        }
    ]


class EmbededDashAF3Plugin(AirflowPlugin):
    name = "embeded_dashboards"

    # fastapi_apps / external_views default to [] on AirflowPlugin and are filled in
    # per instance below, since both depend on Airflow variables read at load time.
    def __init__(self) -> None:
        super().__init__()
        ensure_airflow_version_supported()
        self.fastapi_apps = [
            {
                "name": "Embedash",
                "app": create_embedash_fastapi_app(),
                "url_prefix": URL_PREFIX,
            }
        ]
        self.external_views = build_external_views()
