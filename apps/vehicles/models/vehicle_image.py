"""VehicleImage – one row per uploaded photo (never multiple paths in one field)."""
from __future__ import annotations

from django.db import models

from .base import TimeStampedModel
from .validators import upload_to_vehicle_image, validate_image_upload


class VehicleImageQuerySet(models.QuerySet):
    def ordered(self) -> "VehicleImageQuerySet":
        return self.order_by("-is_primary", "order", "id")


class VehicleImage(TimeStampedModel):
    vehicle = models.ForeignKey(
        "vehicles.Vehicle", on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(
        upload_to=upload_to_vehicle_image, validators=[validate_image_upload]
    )
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(
        default=0, help_text="Lower numbers display first."
    )
    is_primary = models.BooleanField(
        default=False, help_text="Used as the thumbnail on listing cards."
    )

    objects = VehicleImageQuerySet.as_manager()

    class Meta:
        ordering = ["-is_primary", "order", "id"]
        verbose_name_plural = "Vehicle images"
        constraints = [
            # At most one primary image per vehicle (enforced at DB level).
            models.UniqueConstraint(
                fields=["vehicle"],
                condition=models.Q(is_primary=True),
                name="unique_primary_image_per_vehicle",
            ),
        ]
        indexes = [
            models.Index(fields=["vehicle", "order"], name="vehimg_order_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.vehicle_id}: image #{self.order}"

    def save(self, *args, **kwargs):
        if self.pk is None and not self.order:
            # Default new images to the end of the gallery.
            last = (
                type(self).objects.filter(vehicle_id=self.vehicle_id)
                .aggregate(models.Max("order"))["order__max"]
            )
            self.order = (last or 0) + 1
        super().save(*args, **kwargs)
        if self.is_primary:
            # Demote any other primary images for this vehicle (single-row update).
            type(self).objects.filter(vehicle=self.vehicle, is_primary=True).exclude(
                pk=self.pk
            ).update(is_primary=False)
