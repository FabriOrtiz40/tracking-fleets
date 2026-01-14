from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from .models import (
    Organization, Driver, Vehicle, LocationHistory,
    Trip, Geofence, GeofenceAlert, MaintenanceRecord
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_email', 'contact_phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'contact_email']
    readonly_fields = ['created_at']


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'license_number', 'organization', 'phone', 'is_available', 'created_at']
    list_filter = ['organization', 'is_available', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'license_number', 'phone']
    readonly_fields = ['created_at']
    autocomplete_fields = ['user', 'organization']

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'


@admin.register(Vehicle)
class VehicleAdmin(GISModelAdmin):
    list_display = ['plate', 'type', 'brand', 'model', 'organization', 'current_driver', 'status', 'fuel_level', 'is_active', 'last_updated']
    list_filter = ['type', 'status', 'is_active', 'organization', 'created_at']
    search_fields = ['plate', 'brand', 'model', 'vin']
    readonly_fields = ['last_updated', 'created_at']
    autocomplete_fields = ['organization', 'current_driver']
    fieldsets = (
        ('Basic Information', {
            'fields': ('organization', 'plate', 'type', 'brand', 'model', 'year', 'vin')
        }),
        ('Status', {
            'fields': ('status', 'is_active', 'current_driver')
        }),
        ('Location & Tracking', {
            'fields': ('last_location', 'last_updated')
        }),
        ('Metrics', {
            'fields': ('fuel_level', 'odometer', 'max_speed')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(LocationHistory)
class LocationHistoryAdmin(GISModelAdmin):
    list_display = ['vehicle', 'timestamp', 'speed', 'heading', 'battery_level', 'is_ignition_on']
    list_filter = ['vehicle', 'timestamp', 'is_ignition_on']
    search_fields = ['vehicle__plate']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    autocomplete_fields = ['vehicle']


@admin.register(Trip)
class TripAdmin(GISModelAdmin):
    list_display = ['id', 'vehicle', 'driver', 'start_time', 'end_time', 'distance', 'status', 'avg_speed']
    list_filter = ['status', 'vehicle__type', 'start_time']
    search_fields = ['vehicle__plate', 'driver__user__first_name', 'driver__user__last_name']
    readonly_fields = ['duration']
    date_hierarchy = 'start_time'
    autocomplete_fields = ['vehicle', 'driver']
    fieldsets = (
        ('Trip Information', {
            'fields': ('vehicle', 'driver', 'status')
        }),
        ('Time', {
            'fields': ('start_time', 'end_time', 'duration')
        }),
        ('Location', {
            'fields': ('start_location', 'end_location')
        }),
        ('Metrics', {
            'fields': ('distance', 'max_speed', 'avg_speed', 'fuel_consumed')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Geofence)
class GeofenceAdmin(GISModelAdmin):
    list_display = ['name', 'organization', 'geofence_type', 'is_active', 'created_at']
    list_filter = ['organization', 'geofence_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    autocomplete_fields = ['organization']


@admin.register(GeofenceAlert)
class GeofenceAlertAdmin(GISModelAdmin):
    list_display = ['vehicle', 'geofence', 'alert_type', 'timestamp', 'acknowledged', 'acknowledged_by']
    list_filter = ['alert_type', 'acknowledged', 'timestamp']
    search_fields = ['vehicle__plate', 'geofence__name']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    autocomplete_fields = ['vehicle', 'geofence', 'acknowledged_by']


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'maintenance_type', 'performed_at', 'cost', 'next_service_date', 'odometer_reading']
    list_filter = ['maintenance_type', 'performed_at', 'next_service_date']
    search_fields = ['vehicle__plate', 'description', 'performed_by']
    readonly_fields = ['created_at']
    date_hierarchy = 'performed_at'
    autocomplete_fields = ['vehicle']
    fieldsets = (
        ('Maintenance Information', {
            'fields': ('vehicle', 'maintenance_type', 'description', 'cost')
        }),
        ('Service Details', {
            'fields': ('odometer_reading', 'performed_at', 'performed_by')
        }),
        ('Next Service', {
            'fields': ('next_service_date', 'next_service_odometer')
        }),
        ('Additional Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )