from django.contrib import admin

from apps.accounts.models import AdminProfile


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "has_photo", "created_at", "updated_at")
    search_fields = ("user__username", "user__first_name", "user__last_name", "phone")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(boolean=True, description="Photo?")
    def has_photo(self, obj: AdminProfile) -> bool:
        return bool(obj.photo)
