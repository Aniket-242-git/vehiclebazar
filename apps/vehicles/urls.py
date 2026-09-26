"""URL configuration for the vehicles app.

Two groups of routes:

1. Public website (server-rendered): home, vehicle listing, detail, categories,
   about, contact page.
2. REST APIs under /api/ (DRF router): vehicles, categories, brands, features.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.vehicles.views import api_views
from apps.vehicles.views.vehicle_detail import about, category_page, contact_us, vehicle_detail
from apps.vehicles.views.vehicle_list import home, vehicle_list

router = DefaultRouter()
router.register("api/vehicles", api_views.VehicleViewSet, basename="vehicle")
router.register("api/categories", api_views.CategoryViewSet, basename="category")
router.register("api/brands", api_views.BrandViewSet, basename="brand")
router.register("api/features", api_views.FeatureViewSet, basename="feature")

urlpatterns = [
    # ------------------------------------------------------------------
    # Public website
    # ------------------------------------------------------------------
    path("", home, name="home"),
    path("vehicles/", vehicle_list, name="vehicle_list"),
    path("vehicles/<slug:slug>/", vehicle_detail, name="vehicle_detail"),
    path("categories/", vehicle_list, name="categories"),
    path("categories/<slug:slug>/", category_page, name="category_page"),
    path("about/", about, name="about"),
    path("contact-us/", contact_us, name="contact_us"),
    # ------------------------------------------------------------------
    # REST API (DRF router: /api/vehicles/, /api/categories/, ...)
    # ------------------------------------------------------------------
    path("", include(router.urls)),
]
