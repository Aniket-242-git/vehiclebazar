"""Contact form submission views.

Flow (per requirements): validate -> save to DB -> dispatch via EmailService.
The service is injected through ``get_email_service()`` so the provider can be
swapped (console/SMTP/SendGrid/SES) without changing this view.
"""
from __future__ import annotations

import logging

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.contacts.serializers import ContactRequestSerializer
from apps.contacts.services import get_email_service
from apps.vehicles.models import Vehicle

logger = logging.getLogger(__name__)


@require_POST
def contact_vehicle_form(request):
    """Server-rendered submit handler from the vehicle detail page."""
    data = {
        "name": request.POST.get("name"),
        "email": request.POST.get("email"),
        "phone": request.POST.get("phone"),
        "message": request.POST.get("message"),
        "vehicle": request.POST.get("vehicle"),
    }
    serializer = ContactRequestSerializer(data=data)
    back = request.POST.get("next") or "/"

    if not serializer.is_valid():
        logger.debug("Invalid contact submission: %s", serializer.errors)
        vehicle_slug = None
        try:
            vehicle_slug = Vehicle.objects.filter(pk=data["vehicle"]).values_list("slug", flat=True).first()
        except (TypeError, ValueError):
            pass
        target = f"/vehicles/{vehicle_slug}/" if vehicle_slug else back
        return render(
            request,
            "public/contact_submit_error.html",
            {"errors": serializer.errors, "form_data": data, "back": target},
            status=400,
        )

    contact_request = serializer.save()
    # Dispatch email through the pluggable service (console prints payload now).
    get_email_service().send_vehicle_contact_email(contact_request)

    messages.success(request, "Your message has been sent! The seller will contact you soon.")
    return redirect(back)
