"""API views for tracking visitor analytics and geolocation."""
from __future__ import annotations

import json
import logging
from decimal import Decimal, InvalidOperation

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.visitors.models import DeviceType, LocationStatus, VisitorLog
from apps.visitors.utils import get_client_ip, parse_user_agent, reverse_geocode

logger = logging.getLogger(__name__)


def _to_decimal(val) -> Decimal | None:
    if val is None or val == "":
        return None
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _to_float(val) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


@csrf_exempt
@require_POST
def track_visit(request):
    """Receive visitor tracking payload from frontend.

    Supports creating a new log on page load, and updating an existing log
    with GPS coordinates once the visitor grants location access.
    """
    try:
        if request.content_type == "application/json" and request.body:
            data = json.loads(request.body.decode("utf-8"))
        else:
            data = request.POST.dict()
    except Exception as exc:
        logger.warning("Invalid JSON in track_visit: %s", exc)
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    visit_id = data.get("visit_id")
    location_enabled = bool(data.get("location_enabled", False))
    location_status = data.get("location_status", LocationStatus.NOT_PROMPTED)
    if location_status not in LocationStatus.values:
        location_status = LocationStatus.GRANTED if location_enabled else LocationStatus.DENIED

    lat_dec = _to_decimal(data.get("latitude"))
    lon_dec = _to_decimal(data.get("longitude"))
    accuracy = _to_float(data.get("accuracy"))

    city = (data.get("city") or "").strip()[:120]
    state_region = (data.get("state") or data.get("state_region") or "").strip()[:120]
    country = (data.get("country") or "").strip()[:120]
    postal_code = (data.get("postal_code") or "").strip()[:30]
    address = (data.get("address") or "").strip()

    # If coordinates are present but address fields are empty, reverse geocode as fallback
    if location_enabled and lat_dec is not None and lon_dec is not None and (not city and not country):
        geo_info = reverse_geocode(float(lat_dec), float(lon_dec))
        city = city or geo_info.get("city", "")[:120]
        state_region = state_region or geo_info.get("state_region", "")[:120]
        country = country or geo_info.get("country", "")[:120]
        postal_code = postal_code or geo_info.get("postal_code", "")[:30]
        address = address or geo_info.get("address", "")

    # Case 1: Update existing visit (e.g. user allowed location after initial ping)
    if visit_id:
        try:
            visit = VisitorLog.objects.get(id=visit_id)
            visit.location_enabled = location_enabled
            visit.location_status = location_status
            if location_enabled:
                visit.latitude = lat_dec
                visit.longitude = lon_dec
                visit.accuracy = accuracy
                visit.city = city
                visit.state_region = state_region
                visit.country = country
                visit.postal_code = postal_code
                visit.address = address
            visit.save()
            return JsonResponse({"status": "ok", "action": "updated", "visit_id": visit.id})
        except VisitorLog.DoesNotExist:
            pass  # Fall through to create new if id not found

    # Case 2: Create new visitor log
    ip_address = get_client_ip(request)
    ua_raw = request.META.get("HTTP_USER_AGENT", "")
    ua_parsed = parse_user_agent(ua_raw)

    session_key = ""
    if request.session:
        if not request.session.session_key:
            try:
                request.session.save()
            except Exception:
                pass
        session_key = request.session.session_key or ""

    user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None

    # Allow client to override screen resolution and language
    screen_resolution = (data.get("screen_resolution") or "").strip()[:30]
    language = (data.get("language") or request.META.get("HTTP_ACCEPT_LANGUAGE", ""))[:30]
    page_url = (data.get("page_url") or request.path)[:500]
    referrer = (data.get("referrer") or request.META.get("HTTP_REFERER", ""))[:500]

    device_type = ua_parsed.get("device_type", DeviceType.DESKTOP)
    if device_type not in DeviceType.values:
        device_type = DeviceType.DESKTOP

    visit = VisitorLog.objects.create(
        session_key=session_key,
        ip_address=ip_address,
        user_agent=ua_raw,
        device_type=device_type,
        os=ua_parsed.get("os", "")[:80],
        browser=ua_parsed.get("browser", "")[:80],
        browser_version=ua_parsed.get("browser_version", "")[:40],
        screen_resolution=screen_resolution,
        language=language,
        page_url=page_url,
        referrer=referrer,
        location_enabled=location_enabled,
        location_status=location_status,
        latitude=lat_dec if location_enabled else None,
        longitude=lon_dec if location_enabled else None,
        accuracy=accuracy if location_enabled else None,
        city=city if location_enabled else "",
        state_region=state_region if location_enabled else "",
        country=country if location_enabled else "",
        postal_code=postal_code if location_enabled else "",
        address=address if location_enabled else "",
        user=user,
    )

    return JsonResponse({"status": "ok", "action": "created", "visit_id": visit.id})
