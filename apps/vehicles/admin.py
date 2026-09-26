"""Django admin registration for the vehicles app.

Gives staff full management of categories, brands, features and vehicles:
multiple image upload via inlines, activate/deactivate + mark-sold actions,
search, filters and list displays tuned for marketplace operations.
"""
from django.contrib import admin
from django.utils.html import format_html

from apps.vehicles.models import Brand, Category, Feature, Vehicle, VehicleImage, VehicleStatus


class VehicleImageInline(admin.TabularInline):
    """Multiple images per vehicle – stored as separate rows (VehicleImage)."""

    model = VehicleImage
    extra = 1
    fields = ("image", "alt_text", "order", "is_primary")
    ordering = ("order", "id")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "vehicle_count", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "description")
    list_editable = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)

    @admin.display(description="Vehicles")
    def vehicle_count(self, obj) -> int:
        return obj.vehicles.count()


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    list_editable = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "thumbnail", "title", "category", "brand", "price_display",
        "status", "is_featured", "is_active", "created_at",
    )
    list_filter = ("status", "is_active", "is_featured", "category", "brand", "fuel_type")
    search_fields = ("title", "model_name", "location", "description", "brand__name", "category__name")
    list_editable = ("is_featured", "is_active")
    list_select_related = ("category", "brand")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("category", "brand")
    inlines = [VehicleImageInline]
    filter_horizontal = ("features",)
    readonly_fields = ("created_at", "updated_at", "preview_image")
    date_hierarchy = "created_at"
    actions = ["mark_available", "mark_sold", "activate", "deactivate"]
    fieldsets = (
        ("Basics", {
            "fields": ("category", "brand", "title", "slug", "model_name", "description"),
        }),
        ("Pricing", {
            "fields": ("price", "offer_price"),
        }),
        ("Specifications", {
            "fields": (
                "manufacturing_year", "registration_year", "km_driven",
                "fuel_type", "transmission", "engine", "color", "ownership",
            ),
        }),
        ("Status & Visibility", {
            "fields": ("status", "is_featured", "is_active", "location"),
        }),
        ("Timestamps", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at", "preview_image"),
        }),
    )

    # ------------------------------------------------------------------
    @admin.display(description="Image")
    def thumbnail(self, obj) -> str:
        img = obj.primary_image
        if img and img.image:
            return format_html('<img src="{}" style="height:42px;width:auto;border-radius:6px;">', img.image.url)
        return "—"

    @admin.display(description="Price", ordering="price")
    def price_display(self, obj) -> str:
        if obj.offer_price:
            return f"₹{obj.offer_price:,.0f} (was ₹{obj.price:,.0f})"
        return f"₹{obj.price:,.0f}"

    @admin.display(description="Primary image")
    def preview_image(self, obj):
        return self.thumbnail(obj)

    # ------------------------------------------------------------------
    # Bulk actions – all single UPDATE queries (no per-row saves).
    # ------------------------------------------------------------------
    @admin.action(description="Mark selected as available")
    def mark_available(self, request, queryset):
        updated = queryset.update(status=VehicleStatus.AVAILABLE)
        self.message_user(request, f"{updated} vehicle(s) marked available.")

    @admin.action(description="Mark selected as sold")
    def mark_sold(self, request, queryset):
        updated = queryset.update(status=VehicleStatus.SOLD)
        self.message_user(request, f"{updated} vehicle(s) marked sold.")

    @admin.action(description="Activate selected")
    def activate(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} vehicle(s) activated.")

    @admin.action(description="Deactivate selected")
    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} vehicle(s) deactivated.")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("category", "brand")
            .prefetch_related("images")
        )
