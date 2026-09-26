"""Offer – promotional campaign shown as a modal on the public site."""
from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.vehicles.models.base import SlugifiedModel, TimeStampedModel
from apps.vehicles.models.validators import upload_to_offer_banner, validate_image_upload


class Offer(TimeStampedModel, SlugifiedModel):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    description = models.TextField()
    banner = models.ImageField(
        upload_to=upload_to_offer_banner,
        blank=True,
        null=True,
        validators=[validate_image_upload],
    )
    button_text = models.CharField(max_length=60, default="Shop Now")
    button_url = models.URLField(blank=True, help_text="Optional link for the CTA button.")

    start_date = models.DateTimeField(help_text="Modal appears from this moment.")
    end_date = models.DateTimeField(help_text="Modal disappears after this moment.")

    is_active = models.BooleanField(default=True, db_index=True)
    # "priority" strategy: higher number wins when several offers are live.
    priority = models.PositiveSmallIntegerField(
        default=0, db_index=True, help_text="Higher value = shown first (priority strategy)."
    )
    # "display_order" strategy: lower number wins.
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-priority", "display_order", "-created_at"]
        indexes = [
            models.Index(fields=["is_active", "start_date", "end_date"], name="offer_window_idx"),
        ]

    def __str__(self) -> str:
        return self.title

    def build_slug_source(self) -> str:
        return self.title

    def clean(self) -> None:
        super().clean()
        errors = {}
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            errors["end_date"] = "End date must be after the start date."
        if errors:
            raise ValidationError(errors)

    # ------------------------------------------------------------------
    @property
    def is_live(self) -> bool:
        """Active AND current time inside the configured window."""
        now = timezone.now()
        return bool(
            self.is_active
            and self.start_date <= now <= self.end_date
        )
