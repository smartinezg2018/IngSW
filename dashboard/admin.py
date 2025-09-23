from django.contrib import admin
from .models import Post, JobOffer, AgentConfig


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "caption", "media_id", "date")
    search_fields = ("caption", "media_id")


@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location", "posted_date", "status")
    list_filter = ("company", "location", "status", "posted_date")
    search_fields = ("title", "company", "location", "description")


@admin.register(AgentConfig)
class AgentConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "updated_at")
    list_editable = ("is_active",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {
            'fields': ('name', 'is_active', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Prevent adding more than one instance
        return not AgentConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the singleton
        return False