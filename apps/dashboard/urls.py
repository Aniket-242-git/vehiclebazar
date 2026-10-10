"""URL configuration for the custom admin panel (/admin-panel/)."""
from django.urls import path

from apps.accounts import views as account_views
from apps.dashboard import entity_views as ev
from apps.dashboard.views import dashboard_view

urlpatterns = [
    path("", dashboard_view.dashboard, name="dashboard"),
    path("login/", dashboard_view.admin_login, name="admin_login"),
    path("logout/", dashboard_view.admin_logout, name="admin_logout"),
    # --- Vehicles -------------------------------------------------------
    path("vehicles/", ev.vehicle_list, name="vehicle_list"),
    path("vehicles/add/", ev.vehicle_form, name="vehicle_add"),
    path("vehicles/<int:pk>/edit/", ev.vehicle_form, name="vehicle_update"),
    path("vehicles/<int:pk>/delete/", ev.vehicle_delete, name="vehicle_delete"),
    path("vehicles/<int:pk>/toggle/<str:action>/", ev.vehicle_toggle, name="vehicle_toggle"),
    path("vehicles/<int:vehicle_pk>/images/add/", ev.vehicle_image_add, name="vehicle_image_add"),
    path("vehicle-images/<int:pk>/delete/", ev.vehicle_image_delete, name="vehicle_image_delete"),
    path("vehicle-images/<int:pk>/primary/", ev.vehicle_image_primary, name="vehicle_image_primary"),
    # --- Categories -----------------------------------------------------
    path("categories/", ev.category_list, name="category_list"),
    path("categories/add/", ev.category_form, name="category_add"),
    path("categories/<int:pk>/edit/", ev.category_form, name="category_edit"),
    path("categories/<int:pk>/delete/", ev.category_delete, name="category_delete"),
    # --- Brands ---------------------------------------------------------
    path("brands/", ev.brand_list, name="brand_list"),
    path("brands/add/", ev.brand_form, name="brand_add"),
    path("brands/<int:pk>/edit/", ev.brand_form, name="brand_edit"),
    path("brands/<int:pk>/delete/", ev.brand_delete, name="brand_delete"),
    # --- Features -------------------------------------------------------
    path("features/", ev.feature_list, name="feature_list"),
    path("features/add/", ev.feature_form, name="feature_add"),
    path("features/<int:pk>/edit/", ev.feature_form, name="feature_edit"),
    path("features/<int:pk>/delete/", ev.feature_delete, name="feature_delete"),
    # --- Offers ---------------------------------------------------------
    path("offers/", ev.offer_list, name="offer_list"),
    path("offers/add/", ev.offer_form, name="offer_add"),
    path("offers/<int:pk>/edit/", ev.offer_form, name="offer_edit"),
    path("offers/<int:pk>/delete/", ev.offer_delete, name="offer_delete"),
    path("offers/<int:pk>/toggle/", ev.offer_toggle, name="offer_toggle"),
    # --- Homepage banner slides (dynamic carousel) -----------------------
    path("banners/", ev.banner_list, name="banner_list"),
    path("banners/add/", ev.banner_form, name="banner_add"),
    path("banners/<int:pk>/edit/", ev.banner_form, name="banner_edit"),
    path("banners/<int:pk>/delete/", ev.banner_delete, name="banner_delete"),
    path("banners/<int:pk>/toggle/", ev.banner_toggle, name="banner_toggle"),
    # --- Admin accounts (profile / password / create another admin) ---------
    path("profile/", account_views.profile_view, name="admin_profile"),
    path(
        "profile/password/",
        account_views.password_change_view,
        name="admin_password_change",
    ),
    path("admins/create/", account_views.create_admin_view, name="admin_create"),
    path(
        "contact-requests/",
        dashboard_view.contact_request_list,
        name="contact_requests",
    ),
    path(
        "contact-requests/<int:pk>/update/",
        dashboard_view.contact_request_update,
        name="contact_request_update",
    ),
]
