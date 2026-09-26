"""Programmatic vehicle management helpers (activate / deactivate / mark sold).

Heavy CRUD lives in the built-in Django admin (apps/vehicles/admin.py) and the
DRF VehicleViewSet (apps/vehicles/views/api_views.py, staff-only). These small
service-style helpers exist so any other layer (management commands, future
panel buttons, scripts) can flip vehicle state without duplicating logic.
"""
from __future__ import annotations

import logging
from typing import Type

from django.db.models import QuerySet

from apps.vehicles.models import Vehicle, VehicleStatus

logger = logging.getLogger(__name__)


class VehicleAdminService:
    """State transitions for vehicles – single source of truth."""

    @staticmethod
    def _base_queryset() -> QuerySet[Vehicle]:
        return Vehicle.objects.select_related("category", "brand")

    @classmethod
    def activate(cls, vehicle_id: int) -> Type[Vehicle] | None:
        return cls._set_flag(vehicle_id, is_active=True)

    @classmethod
    def deactivate(cls, vehicle_id: int) -> Type[Vehicle] | None:
        return cls._set_flag(vehicle_id, is_active=False)

    @classmethod
    def mark_sold(cls, vehicle_id: int) -> Vehicle | None:
        return cls._set_status(vehicle_id, VehicleStatus.SOLD)

    @classmethod
    def mark_available(cls, vehicle_id: int) -> Vehicle | None:
        return cls._set_status(vehicle_id, VehicleStatus.AVAILABLE)

    # ------------------------------------------------------------------
    @classmethod
    def _set_flag(cls, vehicle_id: int, *, is_active: bool) -> Vehicle | None:
        vehicle = cls._base_queryset().filter(pk=vehicle_id).first()
        if vehicle is None:
            logger.warning("activate/deactivate: vehicle %s not found", vehicle_id)
            return None
        if vehicle.is_active != is_active:
            vehicle.is_active = is_active
            vehicle.save(update_fields=["is_active", "updated_at"])
            logger.info("Vehicle #%s active=%s", vehicle.pk, is_active)
        return vehicle

    @classmethod
    def _set_status(cls, vehicle_id: int, status: str) -> Vehicle | None:
        vehicle = cls._base_queryset().filter(pk=vehicle_id).first()
        if vehicle is None:
            logger.warning("status change: vehicle %s not found", vehicle_id)
            return None
        if vehicle.status != status:
            vehicle.status = status
            vehicle.save(update_fields=["status", "updated_at"])
            logger.info("Vehicle #%s status=%s", vehicle.pk, status)
        return vehicle
