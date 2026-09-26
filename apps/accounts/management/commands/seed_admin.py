"""Seed (or reset) the initial superuser from environment variables.

Usage:
    python manage.py seed_admin                  # reads .env / environment
    python manage.py seed_admin --username admin --password S3cret!  # explicit

Credentials are taken from (in priority order): CLI flags > environment
variables seeded via dotenv (.env, template: .env.example):

    SEED_ADMIN_USERNAME   (default: admin)
    SEED_ADMIN_PASSWORD   (required unless --password is passed)
    SEED_ADMIN_EMAIL      (optional)
    SEED_ADMIN_FIRST_NAME / SEED_ADMIN_LAST_NAME (optional)

Idempotent: if the user exists it is left untouched unless --update-password
is given. Never commit real credentials; keep them in .env only.
"""
from __future__ import annotations

import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the initial admin/superuser using values from .env"

    def add_arguments(self, parser):
        parser.add_argument("--username", default=None)
        parser.add_argument("--password", default=None)
        parser.add_argument("--email", default="")
        parser.add_argument("--first-name", default="")
        parser.add_argument("--last-name", default="")
        parser.add_argument(
            "--update-password",
            action="store_true",
            help="Reset the password if the user already exists.",
        )

    def handle(self, *args, **opts):
        username = (
            opts["username"]
            or os.getenv("SEED_ADMIN_USERNAME", "admin").strip()
        )
        password = opts["password"] or os.getenv("SEED_ADMIN_PASSWORD", "").strip()
        email = opts["email"] or os.getenv("SEED_ADMIN_EMAIL", "").strip()
        first_name = opts["first_name"] or os.getenv("SEED_ADMIN_FIRST_NAME", "").strip()
        last_name = opts["last_name"] or os.getenv("SEED_ADMIN_LAST_NAME", "").strip()

        if not password:
            raise CommandError(
                "No password provided. Set SEED_ADMIN_PASSWORD in your .env "
                "(see .env.example) or pass --password."
            )

        user = User.objects.filter(username__iexact=username).first()
        if user is None:
            user = User.objects.create_superuser(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Superuser '{username}' created successfully.")
            )
        else:
            if opts["update_password"]:
                user.set_password(password)
                fields = ["password"]
                if email:
                    user.email, fields = email, fields + ["email"]
                user.save(update_fields=fields)
                self.stdout.write(
                    self.style.WARNING(
                        f"User '{username}' already existed - password updated."
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"User '{username}' already exists - nothing changed. "
                        "Use --update-password to reset it."
                    )
                )

        # Profile row is auto-created by signal for new users; ensure for old ones.
        from apps.accounts.models import get_or_create_profile

        get_or_create_profile(user)
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Login at /admin-panel/login/ with username '{username}'."
            )
        )
