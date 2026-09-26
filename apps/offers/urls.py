"""Offer URL routes."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.offers.views.offer_view import OfferViewSet

router = DefaultRouter()
router.register("api/admin/offers", OfferViewSet, basename="offer-admin")

urlpatterns = [
    path("", include(router.urls)),
]
