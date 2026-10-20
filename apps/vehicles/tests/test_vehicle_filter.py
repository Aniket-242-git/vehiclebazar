"""Tests for vehicle listing filters, parameter parsing, and template rendering."""
from django.http import QueryDict
from django.test import TestCase
from django.urls import reverse

from apps.vehicles.models import Brand, Category, Vehicle, VehicleStatus
from apps.vehicles.repositories import VehicleRepository
from apps.vehicles.services.vehicle_service import VehicleService


class VehicleFilterTests(TestCase):
    def setUp(self):
        self.cat_ev = Category.objects.create(name="Electric Vehicles", slug="electric-vehicles", is_active=True)
        self.cat_sedan = Category.objects.create(name="Sedans", slug="sedans", is_active=True)
        self.brand_tata = Brand.objects.create(name="Tata", slug="tata", is_active=True)

        self.v_ev_mumbai = Vehicle.objects.create(
            title="Tata Nexon EV",
            model_name="Nexon EV",
            slug="tata-nexon-ev",
            category=self.cat_ev,
            brand=self.brand_tata,
            price=1500000,
            km_driven=10000,
            location="Mumbai",
            manufacturing_year=2023,
            is_active=True,
            status=VehicleStatus.AVAILABLE,
        )
        self.v_ev_pune = Vehicle.objects.create(
            title="Tata Tiago EV",
            model_name="Tiago EV",
            slug="tata-tiago-ev",
            category=self.cat_ev,
            brand=self.brand_tata,
            price=900000,
            km_driven=12000,
            location="Pune",
            manufacturing_year=2023,
            is_active=True,
            status=VehicleStatus.AVAILABLE,
        )
        self.v_sedan_pune = Vehicle.objects.create(
            title="Tata Tigor Petrol",
            model_name="Tigor",
            slug="tata-tigor-petrol",
            category=self.cat_sedan,
            brand=self.brand_tata,
            price=700000,
            km_driven=25000,
            location="Pune",
            manufacturing_year=2022,
            is_active=True,
            status=VehicleStatus.AVAILABLE,
        )

    def test_parse_params_handles_none_and_null_strings(self):
        qd = QueryDict(
            "sort=latest&q=&category=electric-vehicles&brand=&min_price=&max_price="
            "&year_from=&fuel_type=&transmission=&location=None"
        )
        params = VehicleService.parse_params(qd)
        self.assertEqual(params.category, "electric-vehicles")
        self.assertIsNone(params.brand)
        self.assertIsNone(params.min_price)
        self.assertIsNone(params.max_price)
        self.assertIsNone(params.year_from)
        self.assertIsNone(params.fuel_type)
        self.assertIsNone(params.transmission)
        self.assertIsNone(params.location)
        self.assertEqual(params.q, "")
        self.assertEqual(params.sort, "latest")

    def test_repository_apply_filters_ignores_none_and_null_strings(self):
        repo = VehicleRepository()
        qs = repo.public_queryset()
        filtered = repo.apply_filters(
            qs,
            category="electric-vehicles",
            location="None",
            brand="null",
            fuel_type="None",
            transmission="null",
        )
        self.assertEqual(filtered.count(), 2)

    def test_user_reported_url_returns_matching_vehicles(self):
        url = (
            reverse("vehicle_list")
            + "?sort=latest&q=&category=electric-vehicles&brand=&min_price=&max_price="
            "&year_from=&fuel_type=&transmission=&location=None"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tata Nexon EV")
        self.assertContains(response, "Tata Tiago EV")
        self.assertNotContains(response, "Tata Tigor Petrol")
        self.assertContains(response, "2 vehicles found")
        self.assertContains(response, "Electric Vehicles for Sale")
        # Ensure location input does not display 'None'
        self.assertNotContains(response, 'value="None"')

    def test_default_vehicle_list_location_input_is_empty(self):
        response = self.client.get(reverse("vehicle_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'value="None"')

    def test_filter_by_valid_location(self):
        url = reverse("vehicle_list") + "?location=Pune"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tata Tiago EV")
        self.assertContains(response, "Tata Tigor Petrol")
        self.assertNotContains(response, "Tata Nexon EV")
        self.assertContains(response, "2 vehicles found")
