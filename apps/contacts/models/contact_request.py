"""ContactRequest – saved whenever a visitor contacts a seller about a vehicle."""
from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.db import models

from apps.vehicles.models.base import TimeStampedModel
from apps.vehicles.models.vehicle import Vehicle


class ContactStatus(models.TextChoices):
    NEW = "new", "New"
    CONTACTED = "contacted", "Contacted"
    CLOSED = "closed", "Closed"


PHONE_RE = re.compile(r"^\+?[0-9][0-9 \-\(\)]{6,17}$")


class ContactRequest(TimeStampedModel):
    name = models.CharField(max_length=120)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=20)
    message = models.TextField(blank=True)
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_requests",
    )
    status = models.CharField(
        max_length=12, choices=ContactStatus.choices, default=ContactStatus.NEW, db_index=True
    )
    admin_notes = models.TextField(blank=True, help_text="Internal notes, not shown to visitors.")

    class Meta:
        ordering = ["-created_at"]  # newest first
        indexes = [
            models.Index(fields=["status", "-created_at"], name="contact_status_created_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.name} → {self.vehicle_id} ({self.status})"

    def clean(self) -> None:
        super().clean()
        if self.phone and not PHONE_RE.match(self.phone.strip()):
            raise ValidationError({"phone": "Enter a valid phone number (7–18 digits, optional + and spaces)."})
