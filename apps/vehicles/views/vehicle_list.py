"""Home page + paginated/filtered/sorted vehicle listing (server-rendered)."""
from __future__ import annotations

from django.conf import settings
from django.db.models import Count
from django.shortcuts import render

from apps.vehicles.models import (
    Brand,
    Category,
    FuelType,
    Transmission,
    VehicleStatus,
)
from apps.vehicles.services.vehicle_service import VehicleService

# Sort options shown on the listing page (value -> label). Values must match
# VehicleRepository.SORT_FIELDS keys; unknown values fall back to "latest".
SORT_CHOICES = [
    ("latest", "Latest"),
    ("oldest", "Oldest"),
    ("price_asc", "Price: Low to High"),
    ("price_desc", "Price: High to Low"),
    ("year_desc", "Newest Model"),
    ("year_asc", "Oldest Model"),
]


def home(request):
    """Landing page – Flipkart/Amazon style.

    Everything shown here is admin-manageable:
      * banner carousel slides (image / GIF / video + discount labels)
      * "shop by category" tiles, deal strip, brand row
      * featured vehicles & latest arrivals
    With no vehicles in the DB yet, an attractive dummy catalogue is shown so
    the page never looks empty; real listings automatically replace it.
    """
    from apps.offers.services import BannerService
    from apps.vehicles.services.home_demo import get_demo_data

    featured = list(VehicleService.featured_vehicles(limit=8))
    latest = list(VehicleService.latest_vehicles(limit=10))
    hot_deal = next((v for v in featured if v.has_discount), featured[0] if featured else None)

    context = {
        "banner_slides": BannerService.live_slides(),
        "featured": featured,
        "latest": latest,
        "hot_deal": hot_deal,
        "categories": Category.objects.filter(is_active=True)[:8],
        "brands": Brand.objects.filter(is_active=True)[:12],
    }

    # Fallback demo data (dummy categories / deals / vehicles) so the new
    # landing sections always render while the admin feeds real records.
    if not featured and not latest:
        context.update(get_demo_data())
        context["show_demo"] = True
    return render(request, "public/home.html", context)


def vehicle_list(request):
    """Browse page with search, combinable filters, sorting and pagination.

    Everything happens at the database level (WHERE / ORDER BY / LIMIT-OFFSET);
    we never load the whole table into Python.
    """
    params = VehicleService.parse_params(request.GET)
    max_size = getattr(settings, "PAGINATION_MAX_PAGE_SIZE", 48)
    object_list, page_obj, _ = VehicleService.paginate(params, max_page_size=max_size)

    # Sidebar data – one small query each, cached-friendly.
    categories = Category.objects.filter(is_active=True).annotate(
        vehicle_count=Count("vehicles", filter=None)
    ).order_by("name")
    brands = Brand.objects.filter(is_active=True).order_by("name")

    context = {
        "vehicles": object_list,
        "page_obj": page_obj,
        "params": params,
        "categories": categories,
        "brands": brands,
        "status_choices": VehicleStatus.choices,
        "fuel_choices": FuelType.choices,
        "transmission_choices": Transmission.choices,
        "sort_choices": SORT_CHOICES,
        "total_count": page_obj.paginator.count if page_obj else 0,
        "querystring": _qs_without(request.GET, ["page"]),
    }
    return render(request, "public/vehicle_list.html", context)


def _qs_without(querydict, drop: list[str]) -> str:
    """Rebuild a query string without given keys (for pagination links)."""
    items = [
        (k, v)
        for k in querydict
        for v in querydict.getlist(k)
        if k not in drop
    ]
    from urllib.parse import urlencode

    return urlencode(items)
