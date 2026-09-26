"""Admin panel views for profile management and creating new admins.

Routes (mounted under /admin-panel/ by apps/dashboard/urls.py):
    /profile/                 view + edit own name, photo, contact info
    /profile/password/        change own password
    /admins/create/           create another admin (requires ADMIN_CREATION_CODE)
"""
from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render

from apps.accounts.forms import (
    CreateAdminForm,
    PasswordChangeForm,
    ProfileUpdateForm,
    get_admin_creation_code,
)
from apps.accounts.models import get_or_create_profile

logger = logging.getLogger(__name__)

staff_required = user_passes_test(
    lambda u: u.is_active and u.is_staff, login_url="admin_login"
)


@login_required
@staff_required
def profile_view(request):
    """Show/update the logged-in admin's profile (name, email, photo...)."""
    profile = get_or_create_profile(request.user)

    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            user = request.user
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.email = form.cleaned_data["email"]
            user.save(update_fields=["first_name", "last_name", "email"])
            form.save()
            messages.success(request, "Profile updated successfully.")
            logger.info("Profile updated by %s", user.get_username())
            return redirect("admin_profile")
    else:
        form = ProfileUpdateForm(instance=profile, user=request.user)

    return render(
        request,
        "admin_panel/profile.html",
        {"form": form, "profile": profile, "active_nav": "profile"},
    )


@login_required
@staff_required
def password_change_view(request):
    """Self-service password change; keeps the current session valid."""
    if request.method == "POST":
        form = PasswordChangeForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Password changed successfully.")
            logger.info("Password changed by %s", request.user.get_username())
            return redirect("admin_profile")
    else:
        form = PasswordChangeForm(user=request.user)

    return render(
        request,
        "admin_panel/password_change.html",
        {"form": form, "active_nav": "profile"},
    )


@login_required
@staff_required
def create_admin_view(request):
    """Create a new staff admin using the unique code from .env."""
    if request.method == "POST":
        form = CreateAdminForm(request.POST, requesting_user=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(
                request, f"Admin '{user.get_username()}' created successfully."
            )
            logger.info(
                "New admin '%s' created by '%s'", user.get_username(),
                request.user.get_username(),
            )
            return redirect("admin_profile")
    else:
        form = CreateAdminForm(requesting_user=request.user)

    return render(
        request,
        "admin_panel/create_admin.html",
        {
            "form": form,
            "creation_enabled": bool(get_admin_creation_code()),
            "active_nav": "admins",
        },
    )
