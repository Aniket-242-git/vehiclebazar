"""Contact URL routes."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.contacts.views.contact_view import contact_vehicle_form

urlpatterns = [
    path("contact/", contact_vehicle_form, name="contact_vehicle_form"),
]
