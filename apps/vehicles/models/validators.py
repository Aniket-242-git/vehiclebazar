"""Upload validation helpers (secure file uploads – shared hosting friendly)."""
from __future__ import annotations

import os

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_image_upload(file) -> None:
    """Validate extension, size and magic-number signature of an upload.

    Never trust the client-provided content type; we sniff the first bytes.
    Animated GIFs are accepted too (used by category tiles / banners).
    """
    max_bytes = getattr(settings, "MAX_UPLOAD_SIZE_MB", 5) * 1024 * 1024
    allowed_ext = getattr(
        settings, "ALLOWED_IMAGE_EXTENSIONS", {"jpg", "jpeg", "png", "webp", "gif"}
    )

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

    signatures = getattr(
        settings,
        "ALLOWED_IMAGE_MAGIC",
        {
            b"\xff\xd8\xff": "image/jpeg",
            b"\x89PNG\r\n\x1a\n": "image/png",
            b"RIFF": "image/webp",
            b"GIF87a": "image/gif",
            b"GIF89a": "image/gif",
        },
    )
    if not any(header.startswith(sig) for sig in signatures):
        raise ValidationError("File content does not look like a valid JPEG/PNG/WEBP/GIF image.")


def validate_media_upload(file) -> None:
    """Validate uploads that may be images (incl. animated GIFs) or videos.

    Used by homepage banner slides: JPG/PNG/WEBP/GIF + MP4/WebM are allowed.
    Still sniffs magic bytes – never trusts the client content type.
    """
    max_bytes = getattr(settings, "MAX_BANNER_UPLOAD_SIZE_MB", 25) * 1024 * 1024
    allowed_ext = {
        "jpg", "jpeg", "png", "webp", "gif",
        "mp4", "m4v", "webm",
    }

    name = getattr(file, "name", "") or ""
    ext = os.path.splitext(name)[1].lower().lstrip(".")
    if ext not in allowed_ext:
        raise ValidationError(
            f"Unsupported file type '.{ext}'. Allowed: {', '.join(sorted(allowed_ext))}."
        )

    size = getattr(file, "size", 0) or 0
    if size > max_bytes:
        raise ValidationError(
            f"File is too large. Maximum allowed size is {max_bytes // (1024 * 1024)} MB."
        )

    pos = file.tell() if hasattr(file, "tell") else 0
    header = file.read(16)
    if hasattr(file, "seek"):
        file.seek(pos)

    image_sigs = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"RIFF", b"GIF87a", b"GIF89a")
    video_sigs = (b"\x1a\x45\xdf\xa3",)  # WebM/Matroska container
    is_ftyp_mp4 = header[4:8] == b"ftyp" and header[:4] == b"\x00\x00"  # MP4 family
    valid = any(header.startswith(s) for s in image_sigs + video_sigs) or is_ftyp_mp4
    if not valid:
        raise ValidationError(
            "File content does not look like a valid image (JPG/PNG/WEBP/GIF) or video (MP4/WebM)."
        )


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
