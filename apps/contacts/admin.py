"""Django admin for contact requests (enquiries)."""
from django.contrib import admin

from apps.contacts.models import ContactRequest, ContactStatus


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "vehicle", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "email", "phone", "message", "vehicle__title")
    list_select_related = ("vehicle",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)  # newest first (requirement #16)
    actions = ["mark_contacted", "mark_closed"]
    fieldsets = (
        ("Enquiry", {"fields": ("name", "email", "phone", "message", "vehicle")}),
        ("Management", {"fields": ("status", "admin_notes")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.action(description="Mark selected as contacted")
    def mark_contacted(self, request, queryset):
        updated = queryset.update(status=ContactStatus.CONTACTED)
        self.message_user(request, f"{updated} enquiry(s) marked contacted.")

    @admin.action(description="Mark selected as closed")
    def mark_closed(self, request, queryset):
        updated = queryset.update(status=ContactStatus.CLOSED)
        self.message_user(request, f"{updated} enquiry(s) closed.")
