"""Tests for visitor tracking and admin panel visitor analytics."""
import json
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.visitors.models import DeviceType, LocationStatus, VisitorLog

User = get_user_model()


class VisitorTrackingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="adminpassword123",
            is_staff=True,
        )

    def test_track_visit_without_location(self):
        """When location is not enabled, record time and device without GPS coordinates."""
        payload = {
            "page_url": "/vehicles/",
            "referrer": "https://google.com",
            "screen_resolution": "1920x1080",
            "language": "en-US",
            "location_enabled": False,
            "location_status": "denied",
        }
        response = self.client.post(
            reverse("track_visit"),
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["action"], "created")
        self.assertIn("visit_id", data)

        visit = VisitorLog.objects.get(id=data["visit_id"])
        self.assertFalse(visit.location_enabled)
        self.assertEqual(visit.location_status, LocationStatus.DENIED)
        self.assertIsNone(visit.latitude)
        self.assertIsNone(visit.longitude)
        self.assertEqual(visit.device_type, DeviceType.DESKTOP)
        self.assertIn("Windows", visit.os)
        self.assertEqual(visit.browser, "Chrome")
        self.assertEqual(visit.screen_resolution, "1920x1080")
        self.assertEqual(visit.page_url, "/vehicles/")

    def test_track_visit_with_location(self):
        """When location is enabled, record coordinates, accuracy, and address."""
        payload = {
            "page_url": "/vehicles/1/",
            "screen_resolution": "390x844",
            "location_enabled": True,
            "location_status": "granted",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "accuracy": 15.5,
            "city": "Mumbai",
            "state": "Maharashtra",
            "country": "India",
            "address": "Mumbai, Maharashtra, India",
        }
        response = self.client.post(
            reverse("track_visit"),
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_USER_AGENT="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")

        visit = VisitorLog.objects.get(id=data["visit_id"])
        self.assertTrue(visit.location_enabled)
        self.assertEqual(visit.location_status, LocationStatus.GRANTED)
        self.assertEqual(visit.city, "Mumbai")
        self.assertEqual(visit.state_region, "Maharashtra")
        self.assertEqual(visit.country, "India")
        self.assertAlmostEqual(float(visit.latitude), 19.0760, places=3)
        self.assertAlmostEqual(float(visit.longitude), 72.8777, places=3)
        self.assertEqual(visit.device_type, DeviceType.MOBILE)
        self.assertIn("iOS", visit.os)
        self.assertIn("https://www.google.com/maps?q=", visit.google_maps_url)

    def test_update_visit_when_user_subsequently_allows_location(self):
        """If visit was initially logged without location, user enabling location updates the record."""
        # Initial ping without location
        initial_payload = {
            "page_url": "/",
            "location_enabled": False,
            "location_status": "prompt_ignored",
        }
        r1 = self.client.post(
            reverse("track_visit"),
            data=json.dumps(initial_payload),
            content_type="application/json",
            HTTP_USER_AGENT="Mozilla/5.0 (Android 14; Mobile) Chrome/129.0",
        )
        self.assertEqual(r1.status_code, 200)
        visit_id = r1.json()["visit_id"]

        visit = VisitorLog.objects.get(id=visit_id)
        self.assertFalse(visit.location_enabled)

        # Subsequent ping with location permission granted by user
        update_payload = {
            "visit_id": visit_id,
            "location_enabled": True,
            "location_status": "granted",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "accuracy": 8.0,
            "city": "New Delhi",
            "country": "India",
        }
        r2 = self.client.post(
            reverse("track_visit"),
            data=json.dumps(update_payload),
            content_type="application/json",
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["action"], "updated")

        visit.refresh_from_db()
        self.assertTrue(visit.location_enabled)
        self.assertEqual(visit.city, "New Delhi")
        self.assertAlmostEqual(float(visit.latitude), 28.6139, places=3)

    def test_admin_visitor_list_view_staff_required(self):
        """Admin panel visitors page requires staff authentication."""
        response = self.client.get(reverse("visitor_list"))
        # Should redirect to admin login
        self.assertEqual(response.status_code, 302)

        # Log in as staff
        self.client.login(username="adminuser", password="adminpassword123")
        response = self.client.get(reverse("visitor_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_panel/visitor_list.html")

    def test_admin_visitor_list_filtering_and_search(self):
        """Filtering by location=enabled or searching matches records properly."""
        # Create sample records
        VisitorLog.objects.create(
            page_url="/about/",
            ip_address="192.168.1.10",
            location_enabled=True,
            city="Bengaluru",
            country="India",
            device_type=DeviceType.MOBILE,
        )
        VisitorLog.objects.create(
            page_url="/contact/",
            ip_address="192.168.1.20",
            location_enabled=False,
            device_type=DeviceType.DESKTOP,
        )

        self.client.login(username="adminuser", password="adminpassword123")

        # Filter location=enabled
        resp_enabled = self.client.get(reverse("visitor_list") + "?location=enabled")
        self.assertEqual(resp_enabled.status_code, 200)
        self.assertEqual(len(resp_enabled.context["visitors"]), 1)
        self.assertEqual(resp_enabled.context["visitors"][0].city, "Bengaluru")

        # Filter location=disabled
        resp_disabled = self.client.get(reverse("visitor_list") + "?location=disabled")
        self.assertEqual(resp_disabled.status_code, 200)
        self.assertEqual(len(resp_disabled.context["visitors"]), 1)
        self.assertFalse(resp_disabled.context["visitors"][0].location_enabled)

        # Search query by city
        resp_search = self.client.get(reverse("visitor_list") + "?q=Bengaluru")
        self.assertEqual(resp_search.status_code, 200)
        self.assertEqual(len(resp_search.context["visitors"]), 1)

    def test_admin_visitor_delete(self):
        """Admin can delete a visitor log record."""
        visit = VisitorLog.objects.create(
            page_url="/test/",
            ip_address="10.0.0.1",
            location_enabled=False,
        )
        self.client.login(username="adminuser", password="adminpassword123")
        resp = self.client.post(reverse("visitor_delete", kwargs={"pk": visit.pk}))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(VisitorLog.objects.filter(pk=visit.pk).exists())
