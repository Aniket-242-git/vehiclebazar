"""DRF permission: staff-only write access."""
from rest_framework.permissions import BasePermission


class IsStaffAdmin(BasePermission):
    """Allow read for anyone, write only for authenticated staff users."""

    def has_permission(self, request, view) -> bool:
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.is_staff)
