"""Root URL configuration for the vehicle marketplace project."""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

# Branding for the built-in Django admin (used by the admin panel pages too).
admin.site.site_header = "Vehicle Marketplace Administration"
admin.site.site_title = "Vehicle Marketplace Admin"
admin.site.index_title = "Manage listings, categories and offers"

urlpatterns = [
    # Built-in Django admin (staff management of users/groups)
    path("django-admin/", admin.site.urls),
    # Custom admin panel + dashboard (staff-only)
    path("admin-panel/", include("apps.dashboard.urls")),
    # Public website + REST APIs
    path("", include("apps.vehicles.urls")),
    path("", include("apps.contacts.urls")),
    path("", include("apps.offers.urls")),
    # DRF browsable API root (handy during development)
    path("api-auth/", include("rest_framework.urls")),
]

# Serve media files through Django only in development; on cPanel the web
# server (Apache/LiteSpeed) serves /media/ directly.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
