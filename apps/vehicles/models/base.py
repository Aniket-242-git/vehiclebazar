"""Shared abstract base model: timestamps + slug helpers (DRY)."""
from django.db import models
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    """Adds created_at / updated_at with sensible indexing for ordering."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class SlugifiedModel(models.Model):
    """Generates a unique slug from a title/name when not provided."""

    slug = models.SlugField(max_length=220, unique=True, db_index=True)

    class Meta:
        abstract = True

    def build_slug_source(self) -> str:  # pragma: no cover - overridden
        raise NotImplementedError

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.build_slug_source())[:200] or "item"
            slug, suffix = base, 1
            qs = type(self)._default_manager.all()
            if self.pk is not None:
                qs = qs.exclude(pk=self.pk)
            while qs.filter(slug=slug).exists():
                suffix += 1
                slug = f"{base}-{suffix}"
            self.slug = slug
        super().save(*args, **kwargs)
