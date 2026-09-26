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

import logging

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.contacts.models import ContactRequest, ContactStatus
from apps.offers.services import OfferService
from apps.vehicles.models import Category, Vehicle, VehicleStatus

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
    context = {
        "stats": stats,
        "contact_stats": contact_stats,
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
