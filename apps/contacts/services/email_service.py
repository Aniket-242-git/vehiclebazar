"""Email service layer (pluggable provider architecture).

Views never contain email logic. They depend on the ``BaseEmailService``
interface; the concrete implementation is chosen from settings via
``get_email_service()``:

    EMAIL_BACKEND_SERVICE = "console"   -> ConsoleEmailService  (default, dev)
    EMAIL_BACKEND_SERVICE = "smtp"      -> SMTPEmailService     (Django email)
    EMAIL_BACKEND_SERVICE = "sendgrid"  -> SendGridEmailService (stub – add key later)

Adding Amazon SES / Mailgun later means writing one new class and registering
it in ``_REGISTRY`` – no view or model changes required.
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:  # pragma: no cover
    from apps.contacts.models import ContactRequest

logger = logging.getLogger(__name__)


class BaseEmailService(ABC):
    """Interface every provider must implement."""

    @abstractmethod
    def send_vehicle_contact_email(self, contact_request: "ContactRequest") -> None:
        ...

    # ------------------------------------------------------------------
    @staticmethod
    def build_payload(contact_request: "ContactRequest") -> dict:
        """Serialise a contact request into an email payload (single source)."""
        vehicle = contact_request.vehicle
        return {
            "to": list(getattr(settings, "CONSOLE_EMAIL_RECIPIENTS", [])),
            "from": getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost"),
            "subject": f"{getattr(settings, 'EMAIL_SUBJECT_PREFIX', '')}New enquiry: {vehicle.title if vehicle else 'General'}",
            "reply_to": contact_request.email,
            "body": (
                f"Name: {contact_request.name}\n"
                f"Email: {contact_request.email}\n"
                f"Phone: {contact_request.phone}\n"
                f"Vehicle: {vehicle.title if vehicle else '-'}\n"
                f"Message: {contact_request.message}"
            ),
            "vehicle_id": vehicle.pk if vehicle else None,
            "contact_request_id": contact_request.pk,
        }


class ConsoleEmailService(BaseEmailService):
    """Temporary implementation: prints the payload to the console/log.

    This is intentionally simple – it will be replaced by SMTP/SendGrid/SES
    without touching any calling code.
    """

    def send_vehicle_contact_email(self, contact_request: "ContactRequest") -> None:
        payload = self.build_payload(contact_request)
        # Requirement: print the email/message payload to the console.
        print("[ConsoleEmailService] Email payload:")  # noqa: T201 (intended)
        print(json.dumps(payload, indent=2, default=str))  # noqa: T201 (intended)
        logger.info("Console email dispatched for contact request #%s", payload["contact_request_id"])


class SMTPEmailService(BaseEmailService):
    """Real provider using Django's e-mail framework (settings.EMAIL_BACKEND)."""

    def send_vehicle_contact_email(self, contact_request: "ContactRequest") -> None:
        from django.core.mail import send_mail

        payload = self.build_payload(contact_request)
        send_mail(
            subject=payload["subject"],
            message=payload["body"],
            from_email=payload["from"],
            recipient_list=payload["to"],
            fail_silently=False,
        )
        logger.info("SMTP email sent for contact request #%s", payload["contact_request_id"])


class SendGridEmailService(BaseEmailService):
    """Stub kept to prove the architecture – plug the SDK in when needed."""

    def send_vehicle_contact_email(self, contact_request: "ContactRequest") -> None:
        raise NotImplementedError(
            "SendGrid integration not configured yet. Set SENDGRID_API_KEY and implement this method."
        )


_REGISTRY: dict[str, type[BaseEmailService]] = {
    "console": ConsoleEmailService,
    "smtp": SMTPEmailService,
    "sendgrid": SendGridEmailService,
}


def get_email_service(name: str | None = None) -> BaseEmailService:
    """Factory used by views/services (dependency-friendly injection point)."""
    key = name or getattr(settings, "EMAIL_BACKEND_SERVICE", "console")
    impl = _REGISTRY.get(key, ConsoleEmailService)
    return impl()
