"""URL configuration for the custom admin panel (/admin-panel/)."""
from django.urls import path

from apps.accounts import views as account_views
from apps.dashboard.views import dashboard_view

urlpatterns = [
    path("", dashboard_view.dashboard, name="dashboard"),
    path("login/", dashboard_view.admin_login, name="admin_login"),
    path("logout/", dashboard_view.admin_logout, name="admin_logout"),
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
