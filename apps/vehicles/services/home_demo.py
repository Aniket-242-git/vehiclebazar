"""Dummy landing-page catalogue used until real vehicles are fed in.

The admin can add up to 50+ vehicles from the panel; while the DB has no
public listings yet, the Flipkart/Amazon-style home page renders this demo
data so it never looks empty. Once real vehicles exist the view ignores
this module automatically (see ``apps.vehicles.views.vehicle_list.home``).

Prices are plain integers – the template formats them with ``floatformat:"g"``
which adds Indian 2-digit grouping (e.g. 825000 -> 8,25,000).
"""
from __future__ import annotations

_IMG = "https://images.unsplash.com/{key}?auto=format&fit=crop&w=640&q=60"


def _car(title, brand, cat, year, km, fuel, trans, price, offer, city, img, badge=""):
    return {
        "title": title, "brand_name": brand, "category_name": cat,
        "manufacturing_year": year, "km_driven": km,
        "fuel_display": fuel, "transmission_display": trans,
        "price": price, "offer_price": offer, "location": city,
        "image": _IMG.format(key=img), "badge": badge,
        "is_featured": bool(badge), "status": "available",
        "url": "/vehicles/",  # demo cards link to the browse page
    }


DEMO_CATEGORIES = [
    {"name": "Cars", "icon": "bi-car-front", "count": 1240, "color": "#2563eb",
     "image": _IMG.format(key="photo-1503376780358-91ff775b806f")},
    {"name": "SUVs", "icon": "bi-truck", "count": 680, "color": "#059669",
     "image": _IMG.format(key="photo-1519641461604-2e4c2cfd7a6e")},
    {"name": "Bikes", "icon": "bi-bicycle", "count": 930, "color": "#ea580c",
     "image": _IMG.format(key="photo-1558979158-65a1eaa08691")},
    {"name": "Scooters", "icon": "bi-lightning-charge", "count": 410, "color": "#7c3aed",
     "image": _IMG.format(key="photo-1558618666-fcd25c85cd64")},
    {"name": "Luxury", "icon": "bi-gem", "count": 150, "color": "#b45309",
     "image": _IMG.format(key="photo-1503736334956-4e8f56a1a2ba")},
    {"name": "Electric", "icon": "bi-plug", "count": 220, "color": "#0891b2",
     "image": _IMG.format(key="photo-1593941707882-a5bba14938c7")},
]

DEAL_OF_THE_DAY = {
    "title": "Honda City ZX · 2021",
    "sub": "i-VTEC · Petrol · 32,000 km · Mumbai",
    "price": 980000, "mrp": 1250000, "discount": "-22%",
    "image": _IMG.format(key="photo-1609521263047-f8f205293fde"),
}

DEMO_OFFERS = [
    {"label": "Certified Inspection", "icon": "bi-patch-check-fill", "color": "#2563eb"},
    {"label": "No-Cost EMI", "icon": "bi-credit-card-fill", "color": "#059669"},
    {"label": "7-Day Money Back", "icon": "bi-arrow-counterclockwise", "color": "#ea580c"},
    {"label": "Free Home Test Drive", "icon": "bi-signpost-split-fill", "color": "#7c3aed"},
]

DEMO_BRANDS = ["Maruti Suzuki", "Hyundai", "Toyota", "Honda", "Tata",
               "Mahindra", "Kia", "BMW", "Mercedes-Benz", "Audi"]

DEMO_FEATURED = [
    _car("Maruti Swift VXi", "Maruti Suzuki", "Hatchback", 2021, 28000,
         "Petrol", "Manual", 620000, 549000, "Delhi",
         "photo-1541899481282-d53b3e01aab7", "Deal of the Day"),
    _car("Hyundai Creta SX(O)", "Hyundai", "SUV", 2022, 34000,
         "Diesel", "Automatic", 1650000, 1495000, "Gurugram",
         "photo-1583121274602-3e2820c69888", "Hot Deal"),
    _car("Toyota Innova Crysta Z", "Toyota", "MUV", 2020, 55000,
         "Diesel", "Automatic", 1990000, 1825000, "Bengaluru",
         "photo-1549317664-bd32c84b7a10", "Featured"),
    _car("Honda Activa 6G", "Honda", "Scooter", 2022, 9000,
         "Petrol", "Automatic", 78000, 69500, "Pune",
         "photo-1558618666-fcd25c85cd64", "Trending"),
    _car("Royal Enfield Classic 350", "Royal Enfield", "Bike", 2021, 14000,
         "Petrol", "Manual", 165000, 149000, "Jaipur",
         "photo-1558979158-65a1eaa08691", "Hot Deal"),
    _car("Tata Nexon XZ+", "Tata", "SUV", 2022, 22000,
         "Diesel", "Manual", 950000, 875000, "Hyderabad",
         "photo-1580273916550-e323be2ae537", "Featured"),
]

DEMO_LATEST = DEMO_FEATURED + [
    _car("Kia Seltos HTX+", "Kia", "SUV", 2021, 41000,
         "Diesel", "Manual", 1350000, 1249000, "Chennai",
         "photo-1605559424843-2e42ee2e7bd7"),
    _car("MG Hector Sharp", "MG", "SUV", 2021, 38000,
         "Diesel", "Automatic", 1420000, 1299000, "Ahmedabad",
         "photo-1533473853777-016a47ad2e44"),
    _car("Yamaha MT-15", "Yamaha", "Bike", 2022, 8000,
         "Petrol", "Manual", 132000, 119000, "Kochi",
         "photo-1568772585437-e1d8a96f5378"),
    _car("VW Polo GT", "Volkswagen", "Hatchback", 2020, 46000,
         "Petrol", "Automatic", 720000, 655000, "Mumbai",
         "photo-1471479917179-f1ffa4e2b91e"),
    _car("BMW 3 Series 320d", "BMW", "Luxury", 2019, 52000,
         "Diesel", "Automatic", 2850000, 2499000, "New Delhi",
         "photo-1555215695-3004980ad54e"),
    _car("Ola S1 Pro (Electric)", "Ola", "Electric", 2023, 4500,
         "Electric", "Automatic", 110000, 92000, "Bengaluru",
         "photo-1593941707882-a5bba14938c7"),
    _car("Mahindra XUV700 AX7", "Mahindra", "SUV", 2023, 12000,
         "Petrol", "Automatic", 2100000, 1950000, "Noida",
         "photo-1617423886154-c53a03acf6a1"),
    _car("Audi A4 Premium", "Audi", "Luxury", 2020, 39000,
         "Petrol", "Automatic", 3200000, 2799000, "Mumbai",
         "photo-1606664515524-ed2f786a0bd6"),
]


def get_demo_data() -> dict:
    """Context payload for the landing page when the DB has no listings yet."""
    return {
        "demo_categories": DEMO_CATEGORIES,
        "demo_deal": DEAL_OF_THE_DAY,
        "demo_offers": DEMO_OFFERS,
        "demo_brands": DEMO_BRANDS,
        "demo_featured": DEMO_FEATURED,
        "demo_latest": DEMO_LATEST,
    }
