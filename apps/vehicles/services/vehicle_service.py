"""Vehicle service – business logic for listing/filter/sort orchestration.

Views stay thin; they translate HTTP -> parameters and call this service.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import QuerySet

from apps.vehicles.models import Vehicle
from apps.vehicles.repositories import VehicleRepository


@dataclass
class VehicleListParams:
    """Parsed, validated query-string parameters (single source of truth)."""

    q: str = ""
    category: Optional[str] = None
    brand: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    year_from: Optional[int] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    sort: str = "latest"
    page: int = 1
    page_size: int = 12
    errors: dict[str, str] = field(default_factory=dict)


class VehicleService:
    repository = VehicleRepository()

    # ------------------------------------------------------------------
    @classmethod
    def parse_params(cls, querydict) -> VehicleListParams:
        q_raw = querydict.get("q", "").strip()
        params = VehicleListParams(q="" if q_raw.lower() in ("none", "null") else q_raw)

        def _str(name: str) -> Optional[str]:
            raw = querydict.get(name)
            if raw in (None, ""):
                return None
            cleaned = str(raw).strip()
            if not cleaned or cleaned.lower() in ("none", "null"):
                return None
            return cleaned

        def _dec(name: str) -> Optional[Decimal]:
            raw = querydict.get(name)
            if raw in (None, ""):
                return None
            cleaned = str(raw).strip()
            if not cleaned or cleaned.lower() in ("none", "null"):
                return None
            try:
                return Decimal(cleaned)
            except InvalidOperation:
                params.errors[name] = "Enter a valid number."
                return None

        def _int(name: str) -> Optional[int]:
            raw = querydict.get(name)
            if raw in (None, ""):
                return None
            cleaned = str(raw).strip()
            if not cleaned or cleaned.lower() in ("none", "null"):
                return None
            try:
                return int(cleaned)
            except (TypeError, ValueError):
                params.errors[name] = "Enter a valid integer."
                return None

        params.category = _str("category")
        params.brand = _str("brand")
        params.min_price = _dec("min_price")
        params.max_price = _dec("max_price")
        params.year_from = _int("year_from")
        params.fuel_type = _str("fuel_type")
        params.transmission = _str("transmission")
        params.location = _str("location")
        params.status = _str("status")
        params.sort = _str("sort") or "latest"
        params.page = _int("page") or 1
        params.page_size = _int("page_size") or 12
        return params

    # ------------------------------------------------------------------
    @classmethod
    def build_queryset(cls, params: VehicleListParams) -> QuerySet[Vehicle]:
        qs = cls.repository.public_queryset()
        qs = cls.repository.search(qs, params.q)
        qs = cls.repository.apply_filters(
            qs,
            category=params.category,
            brand=params.brand,
            min_price=params.min_price,
            max_price=params.max_price,
            year_from=params.year_from,
            fuel_type=params.fuel_type,
            transmission=params.transmission,
            location=params.location,
            status=params.status,
        )
        return cls.repository.apply_sort(qs, params.sort)

    @classmethod
    def paginate(
        cls, params: VehicleListParams, max_page_size: int = 48
    ) -> tuple[QuerySet[Vehicle], Any, list[int]]:
        """Database-level pagination via LIMIT/OFFSET."""
        qs = cls.build_queryset(params)
        paginator = Paginator(qs, min(max(params.page_size, 1), max_page_size))
        try:
            page_obj = paginator.get_page(params.page)
        except (PageNotAnInteger, EmptyPage):  # pragma: no cover - get_page handles
            page_obj = paginator.get_page(1)
        window = list(
            page_obj.paginator.elided_page_range
            if hasattr(page_obj.paginator, "elided_page_range")
            else []
        )
        return page_obj.object_list, page_obj, window

    # ------------------------------------------------------------------
    @classmethod
    def featured_vehicles(cls, limit: int = 6) -> QuerySet[Vehicle]:
        return cls.repository.featured(limit)

    @classmethod
    def latest_vehicles(cls, limit: int = 6) -> QuerySet[Vehicle]:
        return cls.repository.latest(limit)

    @classmethod
    def get_detail(cls, slug: str):
        return cls.repository.by_slug(slug).first()
