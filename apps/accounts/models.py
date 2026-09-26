"""Profile model for admin/staff users.

Django's built-in User is kept (no custom user model swap — safer for an
existing project and for shared hosting migrations). Extra profile data
(photo etc.) lives in a OneToOne profile linked with a signal.
"""
from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


def admin_photo_path(instance, filename: str) -> str:
    """Store admin photos under media/admin_profiles/<username>/."""
    return f"admin_profiles/{instance.user.username}/{filename}"


class AdminProfile(models.Model):
    """One-to-one extension of the auth User for staff accounts."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    photo = models.ImageField(
        "Profile photo",
        upload_to=admin_photo_path,
        blank=True,
        help_text="JPG/PNG/WebP, max 2 MB.",
    )
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Admin profile"
        verbose_name_plural = "Admin profiles"

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"Profile of {self.user.get_username()}"

    @property
    def display_name(self) -> str:
        return self.user.get_full_name() or self.user.get_username()


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance: User, created: bool, **kwargs):
    """Ensure every user gets a profile row (lazily safe via get_or_create)."""
    if created:
        AdminProfile.objects.create(user=instance)


def get_or_create_profile(user: User) -> AdminProfile:
    profile = getattr(user, "profile", None)
    if profile is None:
        profile = AdminProfile.objects.create(user=user)
    return profile
