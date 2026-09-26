"""Upload validation helpers (secure file uploads – shared hosting friendly)."""
from __future__ import annotations

import os

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_image_upload(file) -> None:
    """Validate extension, size and magic-number signature of an upload.

    Never trust the client-provided content type; we sniff the first bytes.
    """
    max_bytes = getattr(settings, "MAX_UPLOAD_SIZE_MB", 5) * 1024 * 1024
    allowed_ext = getattr(settings, "ALLOWED_IMAGE_EXTENSIONS", {"jpg", "jpeg", "png", "webp"})

    name = getattr(file, "name", "") or ""
    ext = os.path.splitext(name)[1].lower().lstrip(".")
    if ext not in allowed_ext:
        raise ValidationError(
            f"Unsupported image type '.{ext}'. Allowed types: {', '.join(sorted(allowed_ext))}."
        )

    size = getattr(file, "size", 0) or 0
    if size > max_bytes:
        raise ValidationError(f"Image is too large. Maximum allowed size is {max_bytes // (1024 * 1024)} MB.")

    pos = file.tell() if hasattr(file, "tell") else 0
    header = file.read(8)
    if hasattr(file, "seek"):
        file.seek(pos)

    signatures = getattr(settings, "ALLOWED_IMAGE_MAGIC", {})
    if not any(header.startswith(sig) for sig in signatures):
        raise ValidationError("File content does not look like a valid JPEG/PNG/WEBP image.")


def upload_to_category(instance, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower().lstrip(".") or "jpg"
    return f"categories/{instance.slug or 'misc'}.{ext}"


def upload_to_vehicle_main(instance, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower().lstrip(".") or "jpg"
    return f"vehicles/logos/{instance.slug or 'misc'}.{ext}"


def upload_to_vehicle_image(instance, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower().lstrip(".") or "jpg"
    vehicle_slug = instance.vehicle.slug if instance.vehicle_id else "unassigned"
    return f"vehicles/{vehicle_slug}/{instance.order if instance.pk is None else instance.pk}.{ext}"


def upload_to_offer_banner(instance, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower().lstrip(".") or "jpg"
    return f"offers/{instance.slug or 'offer'}.{ext}"
