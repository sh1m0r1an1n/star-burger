from django.contrib import admin
from .models import GeoPlace


@admin.register(GeoPlace)
class GeoPlaceAdmin(admin.ModelAdmin):
    list_display = ['address', 'latitude', 'longitude', 'requested_at']
    list_filter = ['requested_at']
    search_fields = ['address']
    readonly_fields = ['requested_at']
    ordering = ['-requested_at']
