"""Vehicle model – the core listing entity."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from .base import SlugifiedModel, TimeStampedModel
from .brand import Brand
from .category import Category
from .feature import Feature


class FuelType(models.TextChoices):
    PETROL = "petrol", "Petrol"
    DIESEL = "diesel", "Diesel"
    CNG = "cng", "CNG"
    ELECTRIC = "electric", "Electric"
    HYBRID = "hybrid", "Hybrid"


class Transmission(models.TextChoices):
    MANUAL = "manual", "Manual"
    AUTOMATIC = "automatic", "Automatic"


class VehicleStatus(models.TextChoices):
    AVAILABLE = "available", "Available"
    SOLD = "sold", "Sold"
    RESERVED = "reserved", "Reserved"
    INACTIVE = "inactive", "Inactive"


class Ownership(models.TextChoices):
    FIRST = "first", "First Owner"
    SECOND = "second", "Second Owner"
    THIRD = "third", "Third Owner"
    FOURTH_PLUS = "fourth_plus", "Fourth Owner or More"


class VehicleQuerySet(models.QuerySet):
    def active(self) -> "VehicleQuerySet":
        """Listings visible to the public: active and not sold/inactive."""
        return self.filter(is_active=True).exclude(status=VehicleStatus.INACTIVE)

    def available(self) -> "VehicleQuerySet":
        return self.active().filter(status=VehicleStatus.AVAILABLE)

    def featured(self) -> "VehicleQuerySet":
        return self.available().filter(is_featured=True)

    def with_related(self) -> "VehicleQuerySet":
        """select_related/prefetch_related to avoid N+1 queries in listings."""
        return (
            self.select_related("category", "brand")
            .prefetch_related("images", "features")
        )


class Vehicle(TimeStampedModel, SlugifiedModel):
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="vehicles"
    )
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="vehicles")
    model_name = models.CharField("Model", max_length=120)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)

    manufacturing_year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1950)]
    )
    registration_year = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1950)]
    )

    price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    offer_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Discounted price. Leave empty for no discount.",
    )

    fuel_type = models.CharField(
        max_length=10, choices=FuelType.choices, default=FuelType.PETROL, db_index=True
    )
    transmission = models.CharField(
        max_length=10,
        choices=Transmission.choices,
        default=Transmission.MANUAL,
        db_index=True,
    )
    km_driven = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    engine_cc = models.PositiveIntegerField("Engine (cc)", null=True, blank=True)
    color = models.CharField(max_length=60, blank=True)
    ownership = models.CharField(
        max_length=15, choices=Ownership.choices, default=Ownership.FIRST
    )
    location = models.CharField(max_length=120, db_index=True)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=10,
        choices=VehicleStatus.choices,
        default=VehicleStatus.AVAILABLE,
        db_index=True,
    )
    is_featured = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # Optional single logo/cover image; the gallery lives in VehicleImage.
    cover_image = models.ImageField(upload_to="vehicles/covers/", blank=True, null=True)

    features = models.ManyToManyField(Feature, blank=True, related_name="vehicles")

    objects = VehicleQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                name="vehicle_offer_price_below_price",
                check=(
                    models.Q(offer_price__isnull=True)
                    | models.Q(offer_price__lt=models.F("price"))
                ),
            ),
            models.CheckConstraint(
                name="vehicle_reg_year_not_before_mfg",
                check=(
                    models.Q(registration_year__isnull=True)
                    | models.Q(registration_year__gte=models.F("manufacturing_year"))
                ),
            ),
        ]
        indexes = [
            models.Index(fields=["is_active", "status"], name="veh_active_status_idx"),
            models.Index(fields=["-created_at"], name="veh_created_desc_idx"),
            models.Index(fields=["price"], name="veh_price_idx"),
            models.Index(fields=["manufacturing_year"], name="veh_mfg_year_idx"),
            models.Index(fields=["is_featured", "is_active"], name="veh_featured_idx"),
            models.Index(fields=["category", "status"], name="veh_cat_status_idx"),
            models.Index(fields=["brand", "status"], name="veh_brand_status_idx"),
        ]

    def __str__(self) -> str:
        return self.title or f"{self.brand_id} {self.model_name}"

    def build_slug_source(self) -> str:
        return self.title or f"{self.brand} {self.model_name} {self.manufacturing_year}"

    # ------------------------------------------------------------------
    # Derived helpers (kept tiny – business logic lives in services)
    # ------------------------------------------------------------------
    @property
    def effective_price(self) -> Decimal:
        return self.offer_price if self.offer_price is not None else self.price

    @property
    def has_discount(self) -> bool:
        return self.offer_price is not None and self.offer_price < self.price

    @property
    def discount_amount(self) -> Decimal:
        return (self.price - self.offer_price) if self.has_discount else Decimal("0")

    @property
    def age_years(self) -> int:
        return max(date.today().year - self.manufacturing_year, 0)

    @property
    def primary_image(self):
        """Thumbnail: explicit primary image, else lowest-order, else cover."""
        images = list(self.images.all()) if self.pk else []
        for img in images:
            if img.is_primary:
                return img
        if images:
            return min(images, key=lambda i: i.order)
        return None

    def get_absolute_url(self) -> str:
        return reverse("vehicle_detail", kwargs={"slug": self.slug})
