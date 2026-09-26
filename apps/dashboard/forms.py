"""Forms for the custom admin panel CRUD screens.

All forms render Bootstrap 5 markup (templates use `form.field` widgets with
the `form-control` / `form-select` classes applied here) so the admin UI is
attractive and consistent – no Django default admin styling leaks in.
"""
from __future__ import annotations

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.contacts.models import ContactRequest
from apps.offers.models import Offer
from apps.vehicles.models import Brand, Category, Feature, Vehicle, VehicleImage


def _bootstrapify(fields) -> None:
    """Apply Bootstrap classes to every widget of a form."""
    for name, field in fields.items():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs.setdefault("class", "form-check-input")
        elif isinstance(widget, forms.SelectMultiple):
            widget.attrs.setdefault("class", "form-select")
            widget.attrs.setdefault("size", "8")
        elif isinstance(widget, forms.Select):
            widget.attrs.setdefault("class", "form-select")
        else:
            widget.attrs.setdefault("class", "form-control")


class BaseAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self.fields)


# ----------------------------------------------------------------------
# Catalogue: categories / brands / features
# ----------------------------------------------------------------------
class CategoryForm(BaseAdminForm):
    class Meta:
        model = Category
        fields = ["name", "description", "image", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class BrandForm(BaseAdminForm):
    class Meta:
        model = Brand
        fields = ["name", "is_active"]


class FeatureForm(BaseAdminForm):
    class Meta:
        model = Feature
        fields = ["name", "icon", "is_active"]


# ----------------------------------------------------------------------
# Vehicles (+ inline gallery management)
# ----------------------------------------------------------------------
class VehicleForm(BaseAdminForm):
    class Meta:
        model = Vehicle
        fields = [
            "title",
            "category",
            "brand",
            "model_name",
            "manufacturing_year",
            "registration_year",
            "price",
            "offer_price",
            "fuel_type",
            "transmission",
            "km_driven",
            "engine_cc",
            "color",
            "ownership",
            "location",
            "description",
            "status",
            "is_featured",
            "is_active",
            "features",
            "cover_image",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "manufacturing_year": forms.NumberInput(
                attrs={"min": 1950, "max": 2100, "placeholder": "e.g. 2021"}
            ),
            "registration_year": forms.NumberInput(
                attrs={"min": 1950, "max": 2100, "placeholder": "Optional"}
            ),
            "km_driven": forms.NumberInput(attrs={"min": 0, "placeholder": "e.g. 45000"}),
        }

    def clean(self):
        cleaned = super().clean()
        price = cleaned.get("price")
        offer = cleaned.get("offer_price")
        if price is not None and offer is not None and offer >= price:
            raise ValidationError(
                "Offer price must be lower than the regular price."
            )
        mfg = cleaned.get("manufacturing_year")
        reg = cleaned.get("registration_year")
        if mfg and reg and reg < mfg:
            raise ValidationError(
                "Registration year cannot be before the manufacturing year."
            )
        return cleaned


class VehicleImageForm(BaseAdminForm):
    """Add an image to an existing vehicle's gallery."""

    class Meta:
        model = VehicleImage
        fields = ["image", "alt_text", "order", "is_primary"]


# ----------------------------------------------------------------------
# Offers
# ----------------------------------------------------------------------
class AdminSplitDateTimeField(forms.SplitDateTimeField):
    """Bootstrap-friendly datetime input (separate date + time boxes)."""

    widget = forms.SplitDateTimeWidget(
        date_format="%Y-%m-%d",
        time_format="%H:%M",
        date_attrs={"type": "date"},
        time_attrs={"type": "time"},
    )


class OfferForm(BaseAdminForm):
    start_date = AdminSplitDateTimeField(label="Starts at")
    end_date = AdminSplitDateTimeField(label="Ends at")

    class Meta:
        model = Offer
        fields = [
            "title",
            "description",
            "banner",
            "button_text",
            "button_url",
            "start_date",
            "end_date",
            "is_active",
            "priority",
            "display_order",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_date"), cleaned.get("end_date")
        if start and end and end <= start:
            raise ValidationError("End date/time must be after the start date/time.")
        return cleaned


# ----------------------------------------------------------------------
# Contact requests
# ----------------------------------------------------------------------
class ContactRequestUpdateForm(BaseAdminForm):
    class Meta:
        model = ContactRequest
        fields = ["status", "admin_notes"]
        widgets = {"admin_notes": forms.Textarea(attrs={"rows": 3})}
