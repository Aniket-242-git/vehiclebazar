"""Vehicle detail page (gallery, specs, features, contact form)."""
from __future__ import annotations

import logging

from django.http import Http404
from django.shortcuts import get_object_or_404, render

from apps.contacts.models import ContactRequest
from apps.contacts.serializers.contact_serializer import ContactRequestFormSerializer
from apps.vehicles.models import Category, Vehicle

logger = logging.getLogger(__name__)


def vehicle_detail(request, slug: str):
    vehicle = get_object_or_404(
        Vehicle.objects.select_related("category", "brand")
        .prefetch_related("images", "features"),
        slug=slug,
        is_active=True,
    )
    similar = (
        Vehicle.objects.select_related("category", "brand")
        .prefetch_related("images")
        .filter(category=vehicle.category, is_active=True)
        .exclude(pk=vehicle.pk)[:4]
    )
    context = {
        "vehicle": vehicle,
        "similar": similar,
        "contact_form": ContactRequestFormSerializer(initial={"vehicle": vehicle.pk}),
    }
    return render(request, "public/vehicle_detail.html", context)


def category_page(request, slug: str):
    """Browse vehicles of one category (reuses listing machinery)."""
    from .vehicle_list import vehicle_list  # local import avoids circulars

    category = get_object_or_404(Category, slug=slug, is_active=True)
    request.GET = request.GET.copy()
    request.GET["category"] = category.slug
    response = vehicle_list(request)
    if hasattr(response, "context_data"):
        response.context_data["active_category"] = category
    return response


def about(request):
    return render(request, "public/about.html", {})


def contact_us(request):
    """General 'Contact' page – not tied to a specific vehicle."""
    if request.method == "POST":
        serializer = ContactRequestFormSerializer(data=request.POST)
        if serializer.is_valid():
            ContactRequest.objects.create(**serializer.validated_data)
            logger.info("General enquiry saved: %s", serializer.validated_data.get("email"))
            return render(request, "public/contact.html", {"success": True})
        return render(request, "public/contact.html", {"form": serializer})
    return render(request, "public/contact.html", {"form": ContactRequestFormSerializer()})
