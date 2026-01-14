from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.auth.models import User
from .models import (
    Vehicle, Trip, Organization, Driver, LocationHistory,
    Geofence, GeofenceAlert, MaintenanceRecord
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class OrganizationSerializer(serializers.ModelSerializer):
    vehicles_count = serializers.SerializerMethodField()
    drivers_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ['id', 'name', 'contact_email', 'contact_phone', 'address',
                  'created_at', 'is_active', 'vehicles_count', 'drivers_count']
        read_only_fields = ['id', 'created_at']

    def get_vehicles_count(self, obj):
        return obj.vehicles.filter(is_active=True).count()

    def get_drivers_count(self, obj):
        return obj.drivers.filter(is_available=True).count()


class DriverSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Driver
        fields = ['id', 'user', 'user_id', 'full_name', 'organization', 'license_number',
                  'phone', 'emergency_contact', 'emergency_phone', 'is_available', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_full_name(self, obj):
        return obj.user.get_full_name()


class DriverListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Driver
        fields = ['id', 'full_name', 'license_number', 'phone', 'is_available']

    def get_full_name(self, obj):
        return obj.user.get_full_name()


class LocationHistorySerializer(GeoFeatureModelSerializer):
    class Meta:
        model = LocationHistory
        geo_field = 'location'
        fields = ['id', 'vehicle', 'timestamp', 'speed', 'heading',
                  'altitude', 'accuracy', 'battery_level', 'is_ignition_on']
        read_only_fields = ['id']


class LocationHistoryCreateSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = LocationHistory
        fields = ['vehicle', 'latitude', 'longitude', 'timestamp', 'speed',
                  'heading', 'altitude', 'accuracy', 'battery_level', 'is_ignition_on']

    def create(self, validated_data):
        from django.contrib.gis.geos import Point
        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')
        validated_data['location'] = Point(longitude, latitude)

        location_history = LocationHistory.objects.create(**validated_data)

        vehicle = validated_data['vehicle']
        vehicle.last_location = validated_data['location']
        vehicle.save(update_fields=['last_location', 'last_updated'])

        return location_history


class VehicleSerializer(serializers.ModelSerializer):
    current_driver = DriverListSerializer(read_only=True)
    current_speed = serializers.SerializerMethodField()
    is_moving = serializers.SerializerMethodField()
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = Vehicle
        fields = ['id', 'organization', 'organization_name', 'plate', 'type', 'brand', 'model',
                  'year', 'vin', 'last_location', 'last_updated', 'current_driver',
                  'fuel_level', 'odometer', 'status', 'is_active', 'max_speed',
                  'current_speed', 'is_moving', 'created_at']
        read_only_fields = ['id', 'last_updated', 'created_at']

    def get_current_speed(self, obj):
        return obj.get_current_speed()

    def get_is_moving(self, obj):
        return obj.is_moving()


class VehicleListSerializer(serializers.ModelSerializer):
    current_driver_name = serializers.SerializerMethodField()
    current_speed = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = ['id', 'plate', 'type', 'brand', 'model', 'status',
                  'last_location', 'last_updated', 'current_driver_name', 'current_speed']

    def get_current_driver_name(self, obj):
        return obj.current_driver.user.get_full_name() if obj.current_driver else None

    def get_current_speed(self, obj):
        return obj.get_current_speed()


class VehicleDetailSerializer(GeoFeatureModelSerializer):
    current_driver = DriverListSerializer(read_only=True)
    recent_locations = serializers.SerializerMethodField()
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = Vehicle
        geo_field = 'last_location'
        fields = ['id', 'organization', 'organization_name', 'plate', 'type', 'brand', 'model',
                  'year', 'vin', 'last_updated', 'current_driver', 'fuel_level',
                  'odometer', 'status', 'is_active', 'max_speed', 'created_at', 'recent_locations']
        read_only_fields = ['id', 'last_updated', 'created_at']

    def get_recent_locations(self, obj):
        recent = obj.location_history.all()[:10]
        return LocationHistorySerializer(recent, many=True).data


class TripSerializer(serializers.ModelSerializer):
    vehicle_plate = serializers.CharField(source='vehicle.plate', read_only=True)
    driver_name = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = ['id', 'vehicle', 'vehicle_plate', 'driver', 'driver_name',
                  'start_time', 'end_time', 'start_location', 'end_location',
                  'distance', 'duration', 'duration_formatted', 'max_speed',
                  'avg_speed', 'fuel_consumed', 'status', 'notes']
        read_only_fields = ['id', 'duration']

    def get_driver_name(self, obj):
        return obj.driver.user.get_full_name() if obj.driver else None

    def get_duration_formatted(self, obj):
        if obj.duration:
            total_seconds = int(obj.duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        return None


class TripDetailSerializer(GeoFeatureModelSerializer):
    vehicle = VehicleListSerializer(read_only=True)
    driver = DriverListSerializer(read_only=True)
    route = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        geo_field = 'start_location'
        fields = ['id', 'vehicle', 'driver', 'start_time', 'end_time',
                  'end_location', 'distance', 'duration', 'max_speed',
                  'avg_speed', 'fuel_consumed', 'status', 'notes', 'route']
        read_only_fields = ['id', 'duration']

    def get_route(self, obj):
        locations = LocationHistory.objects.filter(
            vehicle=obj.vehicle,
            timestamp__gte=obj.start_time,
            timestamp__lte=obj.end_time if obj.end_time else timezone.now()
        ).order_by('timestamp')
        return LocationHistorySerializer(locations, many=True).data


class GeofenceSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Geofence
        geo_field = 'center'
        fields = ['id', 'organization', 'name', 'description', 'geofence_type',
                  'radius', 'polygon', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class GeofenceAlertSerializer(serializers.ModelSerializer):
    vehicle_plate = serializers.CharField(source='vehicle.plate', read_only=True)
    geofence_name = serializers.CharField(source='geofence.name', read_only=True)
    acknowledged_by_name = serializers.SerializerMethodField()

    class Meta:
        model = GeofenceAlert
        fields = ['id', 'geofence', 'geofence_name', 'vehicle', 'vehicle_plate',
                  'alert_type', 'timestamp', 'location', 'acknowledged',
                  'acknowledged_at', 'acknowledged_by', 'acknowledged_by_name']
        read_only_fields = ['id', 'timestamp']

    def get_acknowledged_by_name(self, obj):
        return obj.acknowledged_by.get_full_name() if obj.acknowledged_by else None


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    vehicle_plate = serializers.CharField(source='vehicle.plate', read_only=True)

    class Meta:
        model = MaintenanceRecord
        fields = ['id', 'vehicle', 'vehicle_plate', 'maintenance_type', 'description',
                  'cost', 'odometer_reading', 'performed_at', 'performed_by',
                  'next_service_date', 'next_service_odometer', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']