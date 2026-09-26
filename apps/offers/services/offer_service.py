"""Offer service – decides WHICH single offer the modal shows.

Configurable business rule (settings.OFFER_DISPLAY_STRATEGY):
  * "priority"      -> highest-priority live offer wins (default)
  * "display_order" -> lowest display_order wins, ties broken by newest

The queryset is filtered at DB level: is_active + start_date <= now <= end_date.
"""
from __future__ import annotations

from typing import Optional

from django.conf import settings
from django.db.models import QuerySet
from django.utils import timezone

from apps.offers.models import Offer


class OfferService:
    @staticmethod
    def live_offers() -> QuerySet[Offer]:
        now = timezone.now()
        return Offer.objects.filter(is_active=True, start_date__lte=now, end_date__gte=now)

    @classmethod
    def get_modal_offer(cls) -> Optional[Offer]:
        """Return the one offer that should open as a modal, or None."""
        qs = cls.live_offers()
        strategy = getattr(settings, "OFFER_DISPLAY_STRATEGY", "priority")
        if strategy == "display_order":
            return qs.order_by("display_order", "-created_at").first()
        # default: priority strategy
        return qs.order_by("-priority", "display_order", "-created_at").first()

    @classmethod
    def active_count(cls) -> int:
        return cls.live_offers().count()
