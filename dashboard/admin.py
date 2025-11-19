from django.contrib import admin
from .models import Post, Field

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("caption", "work_field", "date")

@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ("field",)