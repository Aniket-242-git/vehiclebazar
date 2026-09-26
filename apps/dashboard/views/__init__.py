"""Dashboard/admin-panel views package."""
from .dashboard_view import (  # noqa: F401
    admin_login,
    admin_logout,
    contact_request_list,
    contact_request_update,
    dashboard,
)

__all__ = [
    "admin_login",
    "admin_logout",
    "contact_request_list",
    "contact_request_update",
    "dashboard",
]
