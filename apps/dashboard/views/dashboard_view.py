"""Custom admin panel – staff-only dashboard and management screens.

Routes (all under /admin-panel/):
    /                  dashboard with marketplace statistics
    /login/            staff login (Django session auth)
    /logout/           end session
    /contact-requests/ view/search/filter enquiries, change status, add notes

Heavy CRUD for vehicles/categories/brands/images/features is delegated to the
built-in Django admin (/django-admin/), customised in apps/*/admin.py; this
panel adds the dashboard + contact-request workflow on top.
"""
from __future__ import annotations

from datetime import timedelta
import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.contacts.models import ContactRequest, ContactStatus
from apps.offers.services import OfferService
from apps.vehicles.models import Category, Vehicle, VehicleStatus
from apps.visitors.models import DeviceType, VisitorLog

logger = logging.getLogger(__name__)

staff_required = user_passes_test(
    lambda u: u.is_active and u.is_staff, login_url="admin_login"
)


# ----------------------------------------------------------------------
# Auth
# ----------------------------------------------------------------------
def admin_login(request):
    """Staff login page using Django's session authentication."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("dashboard")

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is None:
            error = "Invalid username or password."
        elif not user.is_staff:
            error = "This area is for staff users only."
        else:
            login(request, user)
            nxt = request.GET.get("next") or "/admin-panel/"
            logger.info("Admin login: %s", username)
            return redirect(nxt)

    return render(request, "admin_panel/login.html", {"error": error})


@require_POST
def admin_logout(request):
    logout(request)
    return redirect("admin_login")


# ----------------------------------------------------------------------
# Dashboard
# ----------------------------------------------------------------------
@login_required
@staff_required
def dashboard(request):
    """Marketplace statistics – each number comes from one aggregate query."""
    stats = Vehicle.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        available=Count("id", filter=Q(status=VehicleStatus.AVAILABLE)),
        sold=Count("id", filter=Q(status=VehicleStatus.SOLD)),
        reserved=Count("id", filter=Q(status=VehicleStatus.RESERVED)),
        featured=Count("id", filter=Q(is_featured=True)),
    )
    contact_stats = ContactRequest.objects.aggregate(
        total=Count("id"),
        new=Count("id", filter=Q(status=ContactStatus.NEW)),
        contacted=Count("id", filter=Q(status=ContactStatus.CONTACTED)),
    )
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    visitor_stats = VisitorLog.objects.aggregate(
        total=Count("id"),
        with_location=Count("id", filter=Q(location_enabled=True)),
        without_location=Count("id", filter=Q(location_enabled=False)),
        today=Count("id", filter=Q(visited_at__gte=today_start)),
    )
    context = {
        "stats": stats,
        "contact_stats": contact_stats,
        "visitor_stats": visitor_stats,
        "total_categories": Category.objects.filter(is_active=True).count(),
        "active_offers": OfferService.active_count(),
        "live_offer": OfferService.get_modal_offer(),
        "recent_vehicles": (
            Vehicle.objects.select_related("category", "brand")
            .order_by("-created_at")[:5]
        ),
        "recent_contacts": (
            ContactRequest.objects.select_related("vehicle")
            .order_by("-created_at")[:5]
        ),
        "recent_visitors": VisitorLog.objects.order_by("-visited_at")[:6],
    }
    return render(request, "admin_panel/dashboard.html", context)


# ----------------------------------------------------------------------
# Contact request management
# ----------------------------------------------------------------------
@login_required
@staff_required
def contact_request_list(request):
    """Newest first; combinable status filter + name/email/phone search."""
    qs = ContactRequest.objects.select_related("vehicle").order_by("-created_at")

    status_filter = request.GET.get("status", "").strip()
    if status_filter in ContactStatus.values:
        qs = qs.filter(status=status_filter)

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q)
        )

    context = {
        "requests": qs,
        "status_choices": ContactStatus.choices,
        "current_status": status_filter,
        "q": q,
        "total": qs.count(),
    }
    return render(request, "admin_panel/contact_requests.html", context)


@login_required
@staff_required
@require_POST
def contact_request_update(request, pk: int):
    """Change status and/or save admin notes on an enquiry."""
    obj = get_object_or_404(ContactRequest, pk=pk)
    new_status = request.POST.get("status", "").strip()
    if new_status in ContactStatus.values:
        obj.status = new_status
    notes = request.POST.get("admin_notes")
    if notes is not None:
        obj.admin_notes = notes
    obj.save(update_fields=["status", "admin_notes"])
    logger.info("Contact request #%s updated by %s", pk, request.user.username)
    return redirect("contact_requests")


# ----------------------------------------------------------------------
# Visitor Analytics Management
# ----------------------------------------------------------------------
@login_required
@staff_required
def visitor_list(request):
    """View and filter all website visitors with location, device, and timestamp."""
    qs = VisitorLog.objects.all().order_by("-visited_at")

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Aggregates for top KPI cards
    metrics = VisitorLog.objects.aggregate(
        total=Count("id"),
        with_location=Count("id", filter=Q(location_enabled=True)),
        without_location=Count("id", filter=Q(location_enabled=False)),
        mobile=Count("id", filter=Q(device_type=DeviceType.MOBILE)),
        desktop=Count("id", filter=Q(device_type=DeviceType.DESKTOP)),
        tablet=Count("id", filter=Q(device_type=DeviceType.TABLET)),
        today=Count("id", filter=Q(visited_at__gte=today_start)),
    )

    # Filter by location status
    loc_filter = request.GET.get("location", "").strip().lower()
    if loc_filter == "enabled":
        qs = qs.filter(location_enabled=True)
    elif loc_filter == "disabled":
        qs = qs.filter(location_enabled=False)

    # Filter by device type
    device_filter = request.GET.get("device", "").strip().lower()
    if device_filter in DeviceType.values:
        qs = qs.filter(device_type=device_filter)

    # Filter by time period
    period = request.GET.get("period", "").strip().lower()
    if period == "today":
        qs = qs.filter(visited_at__gte=today_start)
    elif period == "7days":
        qs = qs.filter(visited_at__gte=now - timedelta(days=7))
    elif period == "30days":
        qs = qs.filter(visited_at__gte=now - timedelta(days=30))

    # Search keyword
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(ip_address__icontains=q)
            | Q(city__icontains=q)
            | Q(state_region__icontains=q)
            | Q(country__icontains=q)
            | Q(postal_code__icontains=q)
            | Q(address__icontains=q)
            | Q(browser__icontains=q)
            | Q(os__icontains=q)
            | Q(page_url__icontains=q)
        )

    # Pagination: 25 logs per page
    paginator = Paginator(qs, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Calculate percentages for progress bars
    total_count = metrics["total"] or 0
    loc_pct = round((metrics["with_location"] / total_count * 100), 1) if total_count else 0
    mobile_pct = round((metrics["mobile"] / total_count * 100), 1) if total_count else 0
    desktop_pct = round((metrics["desktop"] / total_count * 100), 1) if total_count else 0

    context = {
        "active_nav": "visitors",
        "page_obj": page_obj,
        "visitors": page_obj.object_list,
        "metrics": metrics,
        "loc_pct": loc_pct,
        "mobile_pct": mobile_pct,
        "desktop_pct": desktop_pct,
        "loc_filter": loc_filter,
        "device_filter": device_filter,
        "period": period,
        "q": q,
        "total_results": qs.count(),
        "device_choices": DeviceType.choices,
    }
    return render(request, "admin_panel/visitor_list.html", context)


@login_required
@staff_required
@require_POST
def visitor_delete(request, pk: int):
    """Delete a single visitor log."""
    visit = get_object_or_404(VisitorLog, pk=pk)
    visit.delete()
    messages.success(request, f"Visitor record #{pk} deleted.")
    return redirect("visitor_list")


@login_required
@staff_required
@require_POST
def visitor_clear(request):
    """Clear or prune visitor logs."""
    scope = request.POST.get("scope", "all")
    if scope == "older_30":
        cutoff = timezone.now() - timedelta(days=30)
        deleted, _ = VisitorLog.objects.filter(visited_at__lt=cutoff).delete()
        messages.success(request, f"Removed {deleted} logs older than 30 days.")
    else:
        deleted, _ = VisitorLog.objects.all().delete()
        messages.success(request, f"Cleared all visitor logs ({deleted} removed).")
    return redirect("visitor_list")

