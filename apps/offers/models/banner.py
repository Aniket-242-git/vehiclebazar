"""Homepage banner slides – fully dynamic carousel managed from the admin panel.

Each slide can be an image, an animated GIF or a looping muted video
(uploaded by the admin). Slides support a badge ("Deal of the Day"), a
discount label ("-40% OFF"), headline/sub-text, a CTA button, a target
link, a scheduled window and ordering – exactly like the promo banners on
Amazon / Flipkart landing pages.
"""
from __future__ import annotations

import os

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.vehicles.models.base import SlugifiedModel, TimeStampedModel
from apps.vehicles.models.validators import validate_media_upload


class BannerSlide(TimeStampedModel, SlugifiedModel):
    class SlideType(models.TextChoices):
        IMAGE = "image", "Image / GIF"
        VIDEO = "video", "Video"

    title = models.CharField(max_length=200, help_text="Internal name / alt text.")
    slug = models.SlugField(max_length=220, unique=True, db_index=True)

    slide_type = models.CharField(
        max_length=8, choices=SlideType.choices, default=SlideType.IMAGE
    )
    image = models.ImageField(
        upload_to="banners/images/",
        blank=True,
        null=True,
        validators=[validate_media_upload],
        help_text="JPG / PNG / WEBP / GIF (animated GIFs supported). Recommended 1600×600.",
    )
    video = models.FileField(
        upload_to="banners/videos/",
        blank=True,
        null=True,
        validators=[validate_media_upload],
        help_text="MP4 / WebM – plays muted & looping in the carousel.",
    )

    # ----- overlay content (all optional, rendered like Flipkart deal banners)
    badge_text = models.CharField(
        max_length=60,
        blank=True,
        default="Big Save",
        help_text='Small pill above the heading, e.g. "Deal of the Day".',
    )
    badge_color = models.CharField(
        max_length=20,
        choices=[
            ("danger", "Red"),
            ("warning", "Yellow"),
            ("success", "Green"),
            ("primary", "Blue"),
            ("dark", "Black"),
        ],
        default="danger",
    )
    discount_label = models.CharField(
        max_length=40,
        blank=True,
        help_text='Discount sticker shown on the slide, e.g. "-40% OFF" or "Flat ₹50,000 Off".',
    )
    heading = models.CharField(max_length=160, blank=True)
    subtext = models.CharField(max_length=255, blank=True)
    cta_text = models.CharField(max_length=60, blank=True, default="Shop Now")
    link_url = models.URLField(blank=True, verbose_name="Link URL")

    # ----- display rules
    start_date = models.DateTimeField(null=True, blank=True, help_text="Leave empty to show immediately.")
    end_date = models.DateTimeField(null=True, blank=True, help_text="Leave empty to keep it live forever.")
    is_active = models.BooleanField(default=True, db_index=True)
    display_order = models.PositiveSmallIntegerField(
        default=0, help_text="Lower numbers appear first in the carousel."
    )

    objects = models.Manager()

    class Meta:
        ordering = ["display_order", "-created_at"]
        verbose_name = "Homepage banner slide"
        verbose_name_plural = "Homepage banner slides"
        indexes = [
            models.Index(fields=["is_active", "display_order"], name="banner_active_order_idx"),
        ]

    def __str__(self) -> str:
        return self.title

    def build_slug_source(self) -> str:
        return self.title

    def clean(self) -> None:
        super().clean()
        errors = {}
        if self.slide_type == self.SlideType.IMAGE and not self.image:
            errors["image"] = "Upload an image/GIF for an image slide."
        if self.slide_type == self.SlideType.VIDEO and not self.video:
            errors["video"] = "Upload a video file for a video slide."
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            errors["end_date"] = "End date must be after the start date."
        if errors:
            raise ValidationError(errors)

    # ------------------------------------------------------------------
    @property
    def media_url(self) -> str:
        if self.slide_type == self.SlideType.VIDEO and self.video:
            return self.video.url
        if self.image:
            return self.image.url
        return ""

    @property
    def has_video(self) -> bool:
        return self.slide_type == self.SlideType.VIDEO and bool(self.video)

    @property
    def is_gif(self) -> bool:
        ext = os.path.splitext(self.image.name)[1].lower() if self.image else ""
        return ext == ".gif"

    @property
    def is_live(self) -> bool:
        """Active AND current time inside the configured window (window optional)."""
        if not self.is_active:
            return False
        now = timezone.now()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True
