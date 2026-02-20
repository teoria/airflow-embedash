import json
import os.path as op
from typing import Any
from urllib.parse import urlsplit
from airflow.models import Variable

from airflow.configuration import conf
from airflow.plugins_manager import AirflowPlugin
from airflow.security import permissions
from airflow.www.auth import has_access
from airflow.www.views import AirflowBaseView
from flask import abort
from flask_appbuilder import AppBuilder, expose
from flask import request, redirect, url_for
import uuid
from airflow.www.app import csrf

MENU_ACCESS_PERMISSIONS = [
    (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
]

 

class EmbededView(AirflowBaseView):  # type: ignore
    default_view = "settings"
    route_base = "/embedash"
    template_folder = "templates" #op.join(op.dirname(__file__), "templates")
    static_folder = op.join(op.dirname(__file__), "static")

    plugin = None  # type: ignore[assignment]

    def create_blueprint(
        self, appbuilder: AppBuilder, endpoint: str | None = None, static_folder: str | None = None
    ) -> None:
        # Make sure the static folder is not overwritten, as we want to use it.
        return super().create_blueprint(appbuilder, endpoint=endpoint, static_folder=self.static_folder)  # type: ignore[no-any-return]

    @expose("/settings")  # type: ignore[untyped-decorator]
    @has_access(MENU_ACCESS_PERMISSIONS)  # type: ignore[untyped-decorator]
    def settings(self) -> Any:
        dashboards = Variable.get("embeded_dashboards", default_var=[], deserialize_json=True)
 
        return self.render_template("settings.html", dashboards=dashboards)  # type: ignore[no-any-return,no-untyped-call]     
        # return self.render_template_string(template, dashboards=dashboards)  # type: ignore[no-any-return,no-untyped-call]     

    @expose("/add_dash", methods=['GET', 'POST'])  # type: ignore[untyped-decorator]
    @has_access(MENU_ACCESS_PERMISSIONS)  # type: ignore[untyped-decorator]
    @csrf.exempt
    def DashboardSettings_add(self) -> Any:
        if request.method == 'POST':
            # Get data from the form fields using their 'name' attributes
            name = request.form.get('name')
            description = request.form.get('description')
            url = request.form.get('url')
            payload = request.form.get('payload',{})
            if payload == "":
                payload = {}
            else:
                payload = json.loads(payload)
            # Perform some action with the data (e.g., save to database, validation)
            if name and description and url:
                # Create a new dashboard object
                new_dashboard = {
                    "id": uuid.uuid4().hex,  # Generate a unique ID for the dashboard
                    "name": name,
                    "description": description,
                    "url": url,
                    "type": "public" if len(payload.items()) == 0 else "private",
                    "payload": payload
                }
                 
                dashboards = Variable.get("embeded_dashboards", default_var=[], deserialize_json=True)
                dashboards.append(new_dashboard) 
                Variable.set(key="embeded_dashboards", value=dashboards, serialize_json=True) 
                return redirect(url_for('EmbededView.settings'))

            else:
                return "Invalid credentials, please try again."
             
   

    @expose("/adddashboard")  # type: ignore[untyped-decorator]
    @has_access(MENU_ACCESS_PERMISSIONS)  # type: ignore[untyped-decorator]
    def DashboardSettings_add_dash(self) -> Any:
        return self.render_template("add_dashboard.html")  # type: ignore[no-any-return,no-untyped-call]
         
   

    @expose("/editdashboard/<id>")  # type: ignore[untyped-decorator]
    @has_access(MENU_ACCESS_PERMISSIONS)  # type: ignore[untyped-decorator]
    def DashboardSettings_edit(self, id: str) -> Any:
         
        dashboards = Variable.get("embeded_dashboards", default_var=[], deserialize_json=True)
        for dashboard in dashboards:
            if dashboard.get("id") == id:
                dash = dashboard
                break
        else:
            dash = None
        return self.render_template("edit_dashboard.html", dashboard=dash)  # type: ignore[no-any-return,no-untyped-call]
    
    @expose("/edit_dash/<id>", methods=['GET', 'POST'])  # type: ignore[untyped-decorator]
    @has_access(MENU_ACCESS_PERMISSIONS)  # type: ignore[untyped-decorator]
    @csrf.exempt
    def DashboardSettings_edit_dash(self, id: str) -> Any:
        if request.method == 'POST':
            # Get data from the form fields using their 'name' attributes

            name = request.form.get('name')
            description = request.form.get('description')
            url = request.form.get('url')
            payload = request.form.get('payload',{})
            if payload == "":
                payload = {}
            else:
                payload = json.loads(payload)
            # Perform some action with the data (e.g., save to database, validation)
            if name and description and url:
                # Create a new dashboard object
                new_dashboard = {
                    "id": id,
                    "name": name,
                    "description": description,
                    "url": url,
                    "type": "public" if len(payload.items()) == 0 else "private",
                    "payload": payload
                }
                 
                dashboards = Variable.get("embeded_dashboards", default_var=[], deserialize_json=True)
                 
                for i, dashboard in enumerate(dashboards):
                    if dashboard.get("id") == id:
                        dashboards[i] = new_dashboard  # Update the existing dashboard with the new data
                        break
 
                Variable.set(key="embeded_dashboards", value=dashboards, serialize_json=True) 
                return redirect(url_for('EmbededView.settings'))

            else:
                return "Invalid credentials, please try again."
             
   



    @expose("/deletedashboard/<id>")  # type: ignore[untyped-decorator]
    @has_access(MENU_ACCESS_PERMISSIONS)  # type: ignore[untyped-decorator]
    def DashboardSettings_delete(self, id: str) -> Any:
        # Here you would add logic to delete the dashboard with the given ID from your database
        # For now, we'll just redirect back to the settings page after "deleting"
         
        dashboards = Variable.get("embeded_dashboards", default_var=[], deserialize_json=True)
        new_dashboards = [dashboard for dashboard in dashboards if dashboard.get("id") != id]
        Variable.set(key="embeded_dashboards", value=new_dashboards, serialize_json=True)
        embeded_view.plugin.refresh_appbuilder_views()
        return redirect(url_for('EmbededView.settings'))
    
    @expose("/view/<id>")  # type: ignore[untyped-decorator]
    @has_access(MENU_ACCESS_PERMISSIONS)  # type: ignore[untyped-decorator]
    def DashboardSettings_view(self, id: str) -> Any:
          
        dashboards = Variable.get("embeded_dashboards", default_var=[], deserialize_json=True)
        for dashboard in dashboards:
            if dashboard.get("id") == id:
                dash = dashboard
                break
        else:
            dash = None

        if dashboard.get("type") == "private":
            payload = dashboard.get("payload", {})
            if payload:
                
                import jwt
                import time

                METABASE_SITE_URL = dashboard.get("url", "")
                METABASE_SECRET_KEY = Variable.get("embeded_dashboards_metabase_token")

                payload["exp"] = round(time.time()) + (60 * 10) # 10 minute expiration
                token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")

                iframeUrl = METABASE_SITE_URL + "/embed/dashboard/" + token + "#bordered=true&titled=true"
                dashboard["url"] = iframeUrl

        return self.render_template("view.html", dashboard=dash)  # type: ignore[no-any-return,no-untyped-call]
      

embeded_view = EmbededView()

from flask import Blueprint
bp = Blueprint(
    "test_plugin",
    __name__,
    template_folder="templates",   # registers airflow/plugins/templates as a Jinja template folder
)

class EmbededDashPlugin(AirflowPlugin):
    name = "embeded_dashboards"
    flask_blueprints = [bp]  # type: ignore[list-item]
    def __init__(self) -> None:  
        embeded_view.plugin = self  # type: ignore[assignment]
        self.refresh_appbuilder_views()
   
    def refresh_appbuilder_views(self) -> None:
        # This method can be called to refresh the appbuilder views based on the current dashboards variable
        menu_label = Variable.get("embeded_dashboards_menu_label", default_var="Dashboards")
        dashboards = Variable.get("embeded_dashboards", default_var=[], deserialize_json=True)
        items = []
        for dashboard in dashboards: 
            items.append(
                {
                    "name": dashboard.get("name", "Unnamed Dashboard"),
                    "category": menu_label,
                    "view": embeded_view,
                    "href": conf.get("webserver", "base_url") + "/embedash/view/"+dashboard.get("id", ""),
                }
            )
        items.append(
            {
                "name": "Settings",
                "category": menu_label,
                "view": embeded_view,
                "href": conf.get("webserver", "base_url") + "/embedash/settings",
            }
        )
        self.appbuilder_views = items 
