"""Django admin for promotional offers (modal banners)."""
from django.contrib import admin
from django.utils.html import format_html

from apps.offers.models import Offer


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("title", "banner", "start_date", "end_date", "priority",
                    "display_order", "is_active", "live_now")
    list_filter = ("is_active",)
    list_editable = ("is_active",)
    search_fields = ("title", "description")
    ordering = ("-priority", "display_order")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Content", {"fields": ("title", "description", "image", "button_text", "button_url")}),
        ("Scheduling", {"fields": ("start_date", "end_date")}),
        ("Display rules", {"fields": ("is_active", "priority", "display_order")}),
        ("Timestamps", {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Banner")
    def banner(self, obj) -> str:
        if obj.image:
            return format_html('<img src="{}" style="height:36px;border-radius:6px;">', obj.image.url)
        return "—"

    @admin.display(description="Live now?", boolean=True)
    def live_now(self, obj) -> bool:
        return obj.is_live()
