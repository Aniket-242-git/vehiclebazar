"""URLs for visitor tracking."""
from django.urls import path
from apps.visitors import views

urlpatterns = [
    path("api/track-visit/", views.track_visit, name="track_visit"),
]
