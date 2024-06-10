from rest_framework import serializers
from .models import Vehicle, Trip

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'plate', 'type', 'last_location', 'last_updated', 'fuel_level', 'is_active']

class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = ['id', 'vehicle', 'start_time', 'end_time', 'start_location', 'end_location', 'distance']