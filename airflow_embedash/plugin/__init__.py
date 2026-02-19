from __future__ import annotations

from typing import TYPE_CHECKING

from airflow import __version__ as airflow_version
from packaging import version

_AIRFLOW3_MAJOR_VERSION = 3

if TYPE_CHECKING:  # pragma: no cover
    from .airflow2 import EmbededDashPlugin as _EmbededDashPluginType
   # from .airflow3 import EmbededDashAF3Plugin as _EmbededDashAF3PluginType

_EmbededDashPlugin: _EmbededDashPluginType  | None = None
# _EmbededDashPlugin: _EmbededDashPluginType | _EmbededDashAF3PluginType | None = None


def __getattr__(name: str) :
    if name == "EmbededDashPlugin":
        global _EmbededDashPlugin
        if _EmbededDashPlugin is None:
            if version.parse(airflow_version).major < _AIRFLOW3_MAJOR_VERSION:
                from .airflow2 import EmbededDashPlugin  # type: ignore[assignment]  # noqa: F401

                _EmbededDashPlugin = EmbededDashPlugin  # type: ignore[assignment]
            # else:
                # _EmbededDashPlugin = EmbededDashPlugin  # type: ignore[assignment]
                # from .airflow3 import EmbededDashAF3Plugin  # type: ignore[assignment]  # noqa: F401

                # _EmbededDashPlugin = EmbededDashAF3Plugin  # type: ignore[assignment]
        return _EmbededDashPlugin
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
