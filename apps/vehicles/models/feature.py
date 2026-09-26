"""Reusable vehicle feature model (Air Conditioning, ABS, Sunroof, ...).

Features are normalised so we never store comma-separated values on Vehicle.
Vehicles link to features via a ManyToManyField (see vehicle.py).
"""
from django.db import models

from .base import SlugifiedModel, TimeStampedModel


class Feature(TimeStampedModel, SlugifiedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    # Optional icon class for the UI (e.g. bootstrap icon name).
    icon = models.CharField(max_length=60, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active", "name"], name="feature_active_idx"),
        ]

    def __str__(self) -> str:
        return self.name

    def build_slug_source(self) -> str:
        return self.name
