from __future__ import annotations

from typing import TYPE_CHECKING, Any

from airflow import __version__ as airflow_version
from packaging import version

_AIRFLOW3_MAJOR_VERSION = 3

if TYPE_CHECKING:  # pragma: no cover
    from .airflow2 import EmbededDashAF2Plugin as _EmbededDashAF2PluginType
    from .airflow3 import EmbededDashAF3Plugin as _EmbededDashAF3PluginType

_EmbededDashPlugin: type[_EmbededDashAF2PluginType | _EmbededDashAF3PluginType] | None = None


def __getattr__(name: str) -> Any:
    if name == "EmbededDashPlugin":
        global _EmbededDashPlugin
        if _EmbededDashPlugin is None:
            if version.parse(airflow_version).major < _AIRFLOW3_MAJOR_VERSION:
                from .airflow2 import EmbededDashAF2Plugin

                _EmbededDashPlugin = EmbededDashAF2Plugin
            else:
                from .airflow3 import EmbededDashAF3Plugin

                _EmbededDashPlugin = EmbededDashAF3Plugin
        return _EmbededDashPlugin
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
