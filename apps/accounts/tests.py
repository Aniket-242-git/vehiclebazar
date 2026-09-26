"""Tests for admin seeding, profile management and create-admin flow."""
from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from apps.accounts.models import AdminProfile


class SeedAdminTests(TestCase):
    def test_seed_creates_superuser(self):
        with self.settings(SEED=None):
            from io import StringIO
            from django.core.management import call_command
            import os
            os.environ["SEED_ADMIN_USERNAME"] = "rootadmin"
            os.environ["SEED_ADMIN_PASSWORD"] = "Root!Pass2026"
            call_command("seed_admin", stdout=StringIO())
        u = User.objects.get(username="rootadmin")
        self.assertTrue(u.is_superuser and u.is_staff)
        self.assertTrue(u.check_password("Root!Pass2026"))
        self.assertTrue(AdminProfile.objects.filter(user=u).exists())

    def test_seed_is_idempotent(self):
        from io import StringIO
        from django.core.management import call_command
        import os
        os.environ["SEED_ADMIN_USERNAME"] = "rootadmin"
        os.environ["SEED_ADMIN_PASSWORD"] = "Other!Pass123"
        User.objects.create_superuser("rootadmin", password="Orig!Pass123")
        out = StringIO()
        call_command("seed_admin", stdout=out)
        self.assertEqual(User.objects.filter(username="rootadmin").count(), 1)
        self.assertTrue(User.objects.get(username="rootadmin").check_password("Orig!Pass123"))


@override_settings()
class ProfileAndCreateAdminTests(TestCase):
    def setUp(self):
        import os
        os.environ["ADMIN_CREATION_CODE"] = "UNIT-CODE-42"
        self.super_user = User.objects.create_superuser(
            "boss", password="Boss!Pass123", first_name="Bossy"
        )
        self.staff = User.objects.create_user(
            "helper", password="Help!Pass123", is_staff=True
        )
        self.client.force_login(self.super_user)

    def test_profile_update(self):
        r = self.client.post("/admin-panel/profile/", {
            "first_name": "New", "last_name": "Name",
            "email": "new@example.com", "phone": "", "bio": "",
        })
        self.assertRedirects(r, "/admin-panel/profile/")
        self.super_user.refresh_from_db()
        self.assertEqual(self.super_user.first_name, "New")

    def test_password_change_requires_old(self):
        r = self.client.post("/admin-panel/profile/password/", {
            "old_password": "nope", "new_password1": "Fresh!Pass123",
            "new_password2": "Fresh!Pass123"})
        self.assertEqual(r.status_code, 200)
        self.super_user.refresh_from_db()
        self.assertFalse(self.super_user.check_password("Fresh!Pass123"))

    def test_create_admin_with_code(self):
        r = self.client.post("/admin-panel/admins/create/", {
            "username": "newbie", "password1": "N3w!Password",
            "password2": "N3w!Password", "creation_code": "UNIT-CODE-42"})
        self.assertEqual(r.status_code, 302)
        u = User.objects.get(username="newbie")
        self.assertTrue(u.is_staff)
        self.assertFalse(u.is_superuser)
        self.assertTrue(AdminProfile.objects.filter(user=u).exists())

    def test_create_admin_bad_code_rejected(self):
        r = self.client.post("/admin-panel/admins/create/", {
            "username": "intruder", "password1": "N3w!Password",
            "password2": "N3w!Password", "creation_code": "wrong"})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username="intruder").exists())

    def test_non_superuser_cannot_create_superuser(self):
        self.client.force_login(self.staff)
        r = self.client.post("/admin-panel/admins/create/", {
            "username": "escalated", "password1": "N3w!Password",
            "password2": "N3w!Password",
            "creation_code": "UNIT-CODE-42", "make_superuser": "on"})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username="escalated").exists())

    def test_anonymous_redirected(self):
        self.client.logout()
        for url in ("/admin-panel/profile/", "/admin-panel/admins/create/"):
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302)
            self.assertIn("/admin-panel/login/", r["Location"])
