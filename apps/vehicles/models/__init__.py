"""Expose all vehicle-related models so Django discovers them correctly."""
from .base import SlugifiedModel, TimeStampedModel
from .brand import Brand
from .category import Category
from .feature import Feature
from .vehicle import FuelType, Ownership, Transmission, Vehicle, VehicleStatus
from .vehicle_image import VehicleImage

__all__ = [
    "Brand",
    "Category",
    "Feature",
    "FuelType",
    "Ownership",
    "SlugifiedModel",
    "TimeStampedModel",
    "Transmission",
    "Vehicle",
    "VehicleImage",
    "VehicleStatus",
]
