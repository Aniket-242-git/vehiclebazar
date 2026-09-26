"""Forms for the admin profile page and admin-creation flow.

Business rules:
* Only a superuser may create another superuser.
* Creating any new staff/admin account requires the ADMIN_CREATION_CODE
  configured in the environment (.env, template: .env.example).
"""
from __future__ import annotations

import os

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from apps.accounts.models import AdminProfile

MAX_PHOTO_SIZE = 2 * 1024 * 1024  # 2 MB
ALLOWED_PHOTO_EXT = (".jpg", ".jpeg", ".png", ".webp")


def get_admin_creation_code() -> str:
    """Read the shared creation code from env on every call (no restart needed)."""
    return os.getenv("ADMIN_CREATION_CODE", "").strip()


class ProfileUpdateForm(forms.ModelForm):
    """Name / email / phone / photo of the logged-in admin."""

    first_name = forms.CharField(label="First name", max_length=150, required=False)
    last_name = forms.CharField(label="Last name", max_length=150, required=False)
    email = forms.EmailField(label="Email")

    class Meta:
        model = AdminProfile
        fields = ["photo", "phone", "bio"]

    def __init__(self, *args, user: User, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if self.initial and not self.data:
            self.initial["first_name"] = user.first_name
            self.initial["last_name"] = user.last_name
            self.initial["email"] = user.email

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if photo:
            name = getattr(photo, "name", "").lower()
            if not name.endswith(ALLOWED_PHOTO_EXT):
                raise ValidationError("Photo must be JPG, PNG or WebP.")
            if photo.size > MAX_PHOTO_SIZE:
                raise ValidationError("Photo must be under 2 MB.")
        return photo


class PasswordChangeForm(forms.Form):
    """Secure self-service password change (verifies the old password)."""

    old_password = forms.CharField(label="Current password", widget=forms.PasswordInput)
    new_password1 = forms.CharField(
        label="New password", widget=forms.PasswordInput, strip=False
    )
    new_password2 = forms.CharField(
        label="Confirm new password", widget=forms.PasswordInput, strip=False
    )

    def __init__(self, *args, user: User, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_old_password(self):
        old = self.cleaned_data["old_password"]
        if not self.user.check_password(old):
            raise ValidationError("Your current password is incorrect.")
        return old

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("new_password1"), cleaned.get("new_password2")
        if p1 and p2 and p1 != p2:
            self.add_error("new_password2", "The two passwords do not match.")
        return cleaned

    def save(self, commit: bool = True) -> User:
        self.user.set_password(self.cleaned_data["new_password1"])
        if commit:
            self.user.save(update_fields=["password"])
        return self.user


class CreateAdminForm(forms.Form):
    """Create a new staff (or superuser) account using the env creation code."""

    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput, strip=False)
    password2 = forms.CharField(
        label="Confirm password", widget=forms.PasswordInput, strip=False
    )
    make_superuser = forms.BooleanField(
        required=False,
        label="Grant full superuser permissions",
        help_text="Only existing superusers can grant this.",
    )
    creation_code = forms.CharField(
        label="Admin creation code",
        widget=forms.PasswordInput(render_value=False),
        help_text="The unique code from the server .env (ADMIN_CREATION_CODE).",
    )

    def __init__(self, *args, requesting_user: User, **kwargs):
        super().__init__(*args, **kwargs)
        self.requesting_user = requesting_user

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_password1(self):
        from django.contrib.auth.password_validation import validate_password

        pwd = self.cleaned_data["password1"]
        validate_password(pwd, self.requesting_user)
        return pwd

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "The two passwords do not match.")

        code = (cleaned.get("creation_code") or "").strip()
        expected = get_admin_creation_code()
        if not expected:
            raise ValidationError(
                "Admin creation is disabled: ADMIN_CREATION_CODE is not set "
                "in the server environment (.env)."
            )
        if code != expected:
            raise ValidationError("Invalid admin creation code.")

        if cleaned.get("make_superuser") and not self.requesting_user.is_superuser:
            raise ValidationError(
                "Only a superuser can create another superuser."
            )
        return cleaned

    def save(self) -> User:
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data["username"],
            password=data["password1"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            email=data.get("email", ""),
            is_staff=True,
            is_superuser=bool(data.get("make_superuser")),
        )
        return user
