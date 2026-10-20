"""Admin-panel CRUD for vehicles, categories, brands, features and offers.

Every screen is protected by staff login; forms/templates are custom
(Bootstrap 5) – nothing here renders the default Django admin UI.
Views stay thin: querysets + shared crud helpers do the work.
"""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.dashboard import crud
from apps.dashboard.forms import (
    BannerSlideForm,
    BrandForm,
    CategoryForm,
    FeatureForm,
    OfferForm,
    VehicleForm,
    VehicleImageForm,
)
from apps.dashboard.views.dashboard_view import staff_required
from apps.offers.models import BannerSlide, Offer
from apps.offers.services import BannerService, OfferService
from apps.vehicles.models import (
    Brand,
    Category,
    Feature,
    Vehicle,
    VehicleImage,
    VehicleStatus,
)


# ======================================================================
# Categories
# ======================================================================
@login_required
@staff_required
def category_list(request):
    return crud.crud_list(
        request,
        queryset=Category.objects.annotate(vehicle_count=Count("vehicles")),
        template_name="admin_panel/category_list.html",
        page_meta={"active_nav": "categories", "page_title": "Categories", "nav_icon": "tags", "singular": "Category", "add_url": "/admin-panel/categories/add/"},
        search_fields=["name", "slug"],
        paginate_by=20,
        order_choices={
            "name": ("name",),
            "-name": ("-name",),
            "newest": ("-created_at",),
            "oldest": ("created_at",),
        },
        default_order=("name",),
    )


@login_required
@staff_required
def category_form(request, pk=None):
    instance = get_object_or_404(Category, pk=pk) if pk else None
    return crud.crud_form(
        request,
        form_class=CategoryForm,
        instance=instance,
        template_name="admin_panel/model_form.html",
        page_meta={"page_title": ("Edit Category" if instance else "Add Category"), "nav_icon": "tags", "list_url": "/admin-panel/categories/", "list_label": "Categories"},
        success_url_name="category_list",
        success_message="Category “%s” saved.",
    )


@login_required
@staff_required
@require_POST
def category_delete(request, pk):
    return crud.crud_delete(
        request, model=Category, pk=pk,
        success_url_name="category_list",
        success_message="Category “%s” deleted.",
    )


# ======================================================================
# Brands
# ======================================================================
@login_required
@staff_required
def brand_list(request):
    return crud.crud_list(
        request,
        queryset=Brand.objects.annotate(vehicle_count=Count("vehicles")),
        template_name="admin_panel/brand_list.html",
        page_meta={"active_nav": "categories", "page_title": "Brands", "nav_icon": "award", "singular": "Brand", "add_url": "/admin-panel/brands/add/"},
        search_fields=["name", "slug"],
        order_choices={"name": ("name",), "-name": ("-name",)},
        default_order=("name",),
    )


@login_required
@staff_required
def brand_form(request, pk=None):
    instance = get_object_or_404(Brand, pk=pk) if pk else None
    return crud.crud_form(
        request,
        form_class=BrandForm,
        instance=instance,
        template_name="admin_panel/model_form.html",
        page_meta={"page_title": ("Edit Brand" if instance else "Add Brand"), "nav_icon": "award", "list_url": "/admin-panel/brands/", "list_label": "Brands", "half_width": ["name"]},
        success_url_name="brand_list",
        success_message="Brand “%s” saved.",
    )


@login_required
@staff_required
@require_POST
def brand_delete(request, pk):
    return crud.crud_delete(
        request, model=Brand, pk=pk,
        success_url_name="brand_list",
        success_message="Brand “%s” deleted.",
    )


# ======================================================================
# Features
# ======================================================================
@login_required
@staff_required
def feature_list(request):
    return crud.crud_list(
        request,
        queryset=Feature.objects.annotate(vehicle_count=Count("vehicles")),
        template_name="admin_panel/feature_list.html",
        page_meta={"active_nav": "categories", "page_title": "Features", "nav_icon": "ui-checks", "singular": "Feature", "add_url": "/admin-panel/features/add/"},
        search_fields=["name", "slug"],
        order_choices={"name": ("name",), "-name": ("-name",)},
        default_order=("name",),
    )


@login_required
@staff_required
def feature_form(request, pk=None):
    instance = get_object_or_404(Feature, pk=pk) if pk else None
    return crud.crud_form(
        request,
        form_class=FeatureForm,
        instance=instance,
        template_name="admin_panel/model_form.html",
        page_meta={"page_title": ("Edit Feature" if instance else "Add Feature"), "nav_icon": "ui-checks", "list_url": "/admin-panel/features/", "list_label": "Features", "half_width": ["name", "icon"]},
        success_url_name="feature_list",
        success_message="Feature “%s” saved.",
    )


@login_required
@staff_required
@require_POST
def feature_delete(request, pk):
    return crud.crud_delete(
        request, model=Feature, pk=pk,
        success_url_name="feature_list",
        success_message="Feature “%s” deleted.",
    )


# ======================================================================
# Vehicles
# ======================================================================
VEHICLE_ORDERS = {
    "newest": ("-created_at",),
    "oldest": ("created_at",),
    "price_low": ("price",),
    "price_high": ("-price",),
    "title": ("title",),
}


def _vehicle_queryset(request):
    qs = Vehicle.objects.select_related("category", "brand")
    status_filter = request.GET.get("status", "").strip()
    if status_filter in VehicleStatus.values:
        qs = qs.filter(status=status_filter)
    cat_filter = request.GET.get("category", "").strip()
    if cat_filter.isdigit():
        qs = qs.filter(category_id=int(cat_filter))
    flag = request.GET.get("flag", "").strip()
    if flag == "featured":
        qs = qs.filter(is_featured=True)
    elif flag == "inactive":
        qs = qs.filter(is_active=False)
    return qs


@login_required
@staff_required
def vehicle_list(request):
    def extra(req):
        return {
            "status_filter": req.GET.get("status", "").strip(),
            "cat_filter": req.GET.get("category", "").strip(),
            "flag_filter": req.GET.get("flag", "").strip(),
            "statuses": VehicleStatus.choices,
            "categories": Category.objects.order_by("name"),
        }

    return crud.crud_list(
        request,
        queryset=_vehicle_queryset(request),
        template_name="admin_panel/vehicle_list.html",
        page_meta={"active_nav": "vehicles", "page_title": "Vehicles", "nav_icon": "car-front", "singular": "Vehicle", "add_url": "/admin-panel/vehicles/add/"},
        search_fields=[
            "title", "model_name", "location",
            "brand__name", "category__name", "slug",
        ],
        paginate_by=15,
        order_choices=VEHICLE_ORDERS,
        default_order=("-created_at",),
        extra_context=extra,
    )


@login_required
@staff_required
def vehicle_form(request, pk=None):
    instance = get_object_or_404(Vehicle, pk=pk) if pk else None
    return crud.crud_form(
        request,
        form_class=VehicleForm,
        instance=instance,
        template_name="admin_panel/vehicle_form.html",
        page_meta={"page_title": ("Edit Vehicle" if instance else "Add Vehicle"), "nav_icon": "car-front", "list_url": "/admin-panel/vehicles/", "list_label": "Vehicles", "half_width": ["category","brand","model_name","manufacturing_year","registration_year","price","offer_price","fuel_type","transmission","km_driven","engine_cc","color","ownership","location","status"]},
        success_url_name="vehicle_list",
        success_message="Vehicle “%s” saved.",
        extra_context={
            "gallery": list(instance.images.ordered()) if instance else [],
        },
    )


@login_required
@staff_required
@require_POST
def vehicle_delete(request, pk):
    return crud.crud_delete(
        request, model=Vehicle, pk=pk,
        success_url_name="vehicle_list",
        success_message="Vehicle “%s” deleted.",
    )


@login_required
@staff_required
@require_POST
def vehicle_toggle(request, pk, action):
    """Quick actions: activate/deactivate, feature/unfeature, mark sold/available."""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if action == "toggle-active":
        vehicle.is_active = not vehicle.is_active
        vehicle.save(update_fields=["is_active", "updated_at"])
        state = "activated" if vehicle.is_active else "deactivated"
        messages.success(request, f"Vehicle {state}.")
    elif action == "toggle-featured":
        vehicle.is_featured = not vehicle.is_featured
        vehicle.save(update_fields=["is_featured", "updated_at"])
        state = "featured" if vehicle.is_featured else "unfeatured"
        messages.success(request, f"Vehicle {state}.")
    elif action == "mark-sold":
        vehicle.status = VehicleStatus.SOLD
        vehicle.save(update_fields=["status", "updated_at"])
        messages.success(request, "Vehicle marked as sold.")
    elif action == "mark-available":
        vehicle.status = VehicleStatus.AVAILABLE
        vehicle.save(update_fields=["status", "updated_at"])
        messages.success(request, "Vehicle marked as available.")
    else:
        messages.error(request, "Unknown action.")
    nxt = request.POST.get("next") or "/admin-panel/vehicles/"
    return redirect(nxt)


# --- Gallery management -------------------------------------------------
@login_required
@staff_required
def vehicle_image_add(request, vehicle_pk):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_pk)
    form = VehicleImageForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        img = form.save(commit=False)
        img.vehicle = vehicle
        img.save()
        messages.success(request, "Image added to gallery.")
        return redirect("vehicle_update", pk=vehicle.pk)
    return render(
        request,
        "admin_panel/vehicle_image_form.html",
        {
            "form": form,
            "vehicle": vehicle,
            "gallery": list(vehicle.images.ordered()),
        },
    )


@login_required
@staff_required
@require_POST
def vehicle_image_delete(request, pk):
    img = get_object_or_404(VehicleImage, pk=pk)
    vehicle_pk = img.vehicle_id
    img.delete()
    messages.success(request, "Image removed.")
    return redirect("vehicle_update", pk=vehicle_pk)


@login_required
@staff_required
@require_POST
def vehicle_image_primary(request, pk):
    img = get_object_or_404(VehicleImage, pk=pk)
    img.is_primary = True
    img.save()  # model save() demotes other primaries automatically
    messages.success(request, "Primary image updated.")
    return redirect("vehicle_update", pk=img.vehicle_id)


# ======================================================================
# Homepage banner slides (dynamic carousel: image / GIF / video)
# ======================================================================
@login_required
@staff_required
def banner_list(request):
    live_ids = {s.id for s in BannerService.live_slides(limit=100)}

    return crud.crud_list(
        request,
        queryset=BannerSlide.objects.all(),
        template_name="admin_panel/banner_list.html",
        page_meta={"active_nav": "banners", "page_title": "Homepage Banners", "nav_icon": "images",
                   "singular": "Banner Slide", "add_url": "/admin-panel/banners/add/"},
        search_fields=["title", "heading", "slug"],
        paginate_by=20,
        order_choices={
            "order": ("display_order", "-created_at"),
            "newest": ("-created_at",),
            "oldest": ("created_at",),
        },
        default_order=("display_order", "-created_at"),
        extra_context=lambda req: {"live_banner_ids": live_ids},
    )


@login_required
@staff_required
def banner_form(request, pk=None):
    instance = get_object_or_404(BannerSlide, pk=pk) if pk else None
    return crud.crud_form(
        request,
        form_class=BannerSlideForm,
        instance=instance,
        template_name="admin_panel/model_form.html",
        page_meta={"page_title": ("Edit Banner Slide" if instance else "Add Banner Slide"),
                   "nav_icon": "images", "list_url": "/admin-panel/banners/", "list_label": "Homepage Banners",
                   "half_width": ["title", "slide_type", "badge_text", "badge_color", "discount_label",
                                  "cta_text", "start_date", "end_date", "display_order"]},
        success_url_name="banner_list",
        success_message="Banner slide “%s” saved.",
    )


@login_required
@staff_required
@require_POST
def banner_delete(request, pk):
    return crud.crud_delete(
        request, model=BannerSlide, pk=pk,
        success_url_name="banner_list",
        success_message="Banner slide “%s” deleted.",
    )


@login_required
@staff_required
@require_POST
def banner_toggle(request, pk):
    slide = get_object_or_404(BannerSlide, pk=pk)
    slide.is_active = not slide.is_active
    slide.save(update_fields=["is_active", "updated_at"])
    state = "activated" if slide.is_active else "deactivated"
    messages.success(request, f"Banner slide {state}.")
    return redirect("banner_list")


# ======================================================================
# Offers
# ======================================================================
@login_required
@staff_required
def offer_list(request):
    live_ids = set(OfferService.live_offers().values_list("id", flat=True))

    return crud.crud_list(
        request,
        queryset=Offer.objects.all(),
        template_name="admin_panel/offer_list.html",
        page_meta={"active_nav": "offers", "page_title": "Offers", "nav_icon": "megaphone", "singular": "Offer", "add_url": "/admin-panel/offers/add/"},
        search_fields=["title", "slug"],
        order_choices={
            "priority": ("-priority", "display_order"),
            "newest": ("-created_at",),
            "start": ("-start_date",),
        },
        default_order=("-priority", "display_order"),
        extra_context=lambda req: {"live_offer_ids": live_ids},
    )


@login_required
@staff_required
def offer_form(request, pk=None):
    instance = get_object_or_404(Offer, pk=pk) if pk else None
    return crud.crud_form(
        request,
        form_class=OfferForm,
        instance=instance,
        template_name="admin_panel/model_form.html",
        page_meta={"page_title": ("Edit Offer" if instance else "Add Offer"), "nav_icon": "megaphone", "list_url": "/admin-panel/offers/", "list_label": "Offers", "half_width": ["title","button_text","start_date","end_date","priority","display_order"]},
        success_url_name="offer_list",
        success_message="Offer “%s” saved.",
    )


@login_required
@staff_required
@require_POST
def offer_delete(request, pk):
    return crud.crud_delete(
        request, model=Offer, pk=pk,
        success_url_name="offer_list",
        success_message="Offer “%s” deleted.",
    )


@login_required
@staff_required
@require_POST
def offer_toggle(request, pk):
    offer = get_object_or_404(Offer, pk=pk)
    offer.is_active = not offer.is_active
    offer.save(update_fields=["is_active", "updated_at"])
    state = "activated" if offer.is_active else "deactivated"
    messages.success(request, f"Offer {state}.")
    return redirect("offer_list")
