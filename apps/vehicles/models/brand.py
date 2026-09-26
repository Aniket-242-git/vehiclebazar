"""Vehicle brand/manufacturer model (Toyota, Honda, Tata, ...)."""
from django.db import models

from .base import SlugifiedModel, TimeStampedModel


class Brand(TimeStampedModel, SlugifiedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Brands"
        indexes = [
            models.Index(fields=["is_active", "name"], name="brand_active_name_idx"),
        ]

    def __str__(self) -> str:
        return self.name

    def build_slug_source(self) -> str:
        return self.name
