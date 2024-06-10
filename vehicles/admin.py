from django.contrib import admin
from .models import Vehicle, Trip

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['plate', 'type', 'last_updated', 'fuel_level', 'is_active']
    list_filter = ['type', 'is_active']
    search_fields = ['plate']

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['id', 'vehicle', 'start_time', 'end_time', 'distance']
    list_filter = ['vehicle__type']
    search_fields = ['vehicle__plate']