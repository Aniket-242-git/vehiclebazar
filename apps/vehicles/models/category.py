"""Vehicle category model (Cars, Bikes, SUVs, ...)."""
from django.db import models

from .base import SlugifiedModel, TimeStampedModel
from .validators import upload_to_category, validate_image_upload


class Category(TimeStampedModel, SlugifiedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, db_index=True)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to=upload_to_category,
        blank=True,
        null=True,
        validators=[validate_image_upload],
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active", "name"], name="cat_active_name_idx"),
        ]

    def __str__(self) -> str:
        return self.name

    def build_slug_source(self) -> str:
        return self.name
