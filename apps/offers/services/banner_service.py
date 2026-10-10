"""Banner service – decides WHICH homepage banner slides appear in the carousel."""
from __future__ import annotations

from typing import List

from django.db.models import Q
from django.utils import timezone

from apps.offers.models import BannerSlide


class BannerService:
    @staticmethod
    def live_slides(limit: int = 12) -> List[BannerSlide]:
        """Active slides whose optional schedule window includes "now"."""
        now = timezone.now()
        return list(
            BannerSlide.objects.filter(is_active=True)
            .filter(
                (Q(start_date__isnull=True) | Q(start_date__lte=now))
                & (Q(end_date__isnull=True) | Q(end_date__gte=now))
            )
            .order_by("display_order", "-created_at")[:limit]
        )
