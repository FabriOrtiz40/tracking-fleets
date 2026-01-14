from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, Max, F
from django.contrib.gis.measure import D
from django.contrib.gis.geos import Point
from datetime import timedelta

from .models import (
    Vehicle, Trip, Organization, Driver, LocationHistory,
    Geofence, GeofenceAlert, MaintenanceRecord
)
from .serializers import (
    VehicleSerializer, VehicleListSerializer, VehicleDetailSerializer,
    TripSerializer, TripDetailSerializer, OrganizationSerializer,
    DriverSerializer, DriverListSerializer, LocationHistorySerializer,
    LocationHistoryCreateSerializer, GeofenceSerializer, GeofenceAlertSerializer,
    MaintenanceRecordSerializer
)


@api_view(['GET'])
def api_root(request):
    return Response({
        'message': 'Bienvenido a la API de Fleet Tracker',
        'endpoints': {
            'organizations': request.build_absolute_uri('organizations/'),
            'drivers': request.build_absolute_uri('drivers/'),
            'vehicles': request.build_absolute_uri('vehicles/'),
            'trips': request.build_absolute_uri('trips/'),
            'locations': request.build_absolute_uri('locations/'),
            'geofences': request.build_absolute_uri('geofences/'),
            'alerts': request.build_absolute_uri('alerts/'),
            'maintenance': request.build_absolute_uri('maintenance/'),
        }
    })


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        organization = self.get_object()
        vehicles = organization.vehicles.filter(is_active=True)
        drivers = organization.drivers.filter(is_available=True)

        active_trips = Trip.objects.filter(
            vehicle__organization=organization,
            status='in_progress'
        ).count()

        moving_vehicles = sum(1 for v in vehicles if v.is_moving())

        return Response({
            'total_vehicles': vehicles.count(),
            'active_vehicles': moving_vehicles,
            'idle_vehicles': vehicles.count() - moving_vehicles,
            'total_drivers': drivers.count(),
            'active_trips': active_trips,
            'maintenance_due': MaintenanceRecord.objects.filter(
                vehicle__organization=organization,
                next_service_date__lte=timezone.now().date() + timedelta(days=7)
            ).count()
        })


class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return DriverListSerializer
        return DriverSerializer

    def get_queryset(self):
        queryset = Driver.objects.all()
        organization_id = self.request.query_params.get('organization', None)
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        is_available = self.request.query_params.get('available', None)
        if is_available:
            queryset = queryset.filter(is_available=is_available.lower() == 'true')
        return queryset

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        driver = self.get_object()
        trips = driver.trips.filter(status='completed')

        total_trips = trips.count()
        total_distance = trips.aggregate(Sum('distance'))['distance__sum'] or 0
        avg_speed = trips.aggregate(Avg('avg_speed'))['avg_speed__avg'] or 0

        return Response({
            'total_trips': total_trips,
            'total_distance': round(total_distance, 2),
            'average_speed': round(avg_speed, 2),
            'current_vehicle': driver.current_vehicle.plate if driver.current_vehicle else None
        })


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return VehicleListSerializer
        elif self.action == 'retrieve':
            return VehicleDetailSerializer
        return VehicleSerializer

    def get_queryset(self):
        queryset = Vehicle.objects.select_related('organization', 'current_driver__user')
        organization_id = self.request.query_params.get('organization', None)
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        vehicle_type = self.request.query_params.get('type', None)
        if vehicle_type:
            queryset = queryset.filter(type=vehicle_type)

        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)

        is_active = self.request.query_params.get('active', None)
        if is_active:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset

    @action(detail=True, methods=['get'])
    def current_location(self, request, pk=None):
        vehicle = self.get_object()
        if not vehicle.last_location:
            return Response({'detail': 'No location data available'}, status=status.HTTP_404_NOT_FOUND)

        latest_location = vehicle.location_history.first()
        serializer = LocationHistorySerializer(latest_location)

        return Response({
            'vehicle': vehicle.plate,
            'location': serializer.data,
            'is_moving': vehicle.is_moving(),
            'current_speed': vehicle.get_current_speed()
        })

    @action(detail=True, methods=['get'])
    def location_history(self, request, pk=None):
        vehicle = self.get_object()
        hours = int(request.query_params.get('hours', 24))
        start_time = timezone.now() - timedelta(hours=hours)

        locations = vehicle.location_history.filter(timestamp__gte=start_time)
        serializer = LocationHistorySerializer(locations, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign_driver(self, request, pk=None):
        vehicle = self.get_object()
        driver_id = request.data.get('driver_id')

        if not driver_id:
            return Response({'error': 'driver_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            driver = Driver.objects.get(id=driver_id)
            if driver.current_vehicle and driver.current_vehicle != vehicle:
                driver.current_vehicle.current_driver = None
                driver.current_vehicle.save()

            vehicle.current_driver = driver
            vehicle.save()

            return Response({'detail': f'Driver {driver.user.get_full_name()} assigned to vehicle {vehicle.plate}'})
        except Driver.DoesNotExist:
            return Response({'error': 'Driver not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def remove_driver(self, request, pk=None):
        vehicle = self.get_object()
        vehicle.current_driver = None
        vehicle.save()
        return Response({'detail': 'Driver removed from vehicle'})

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')
        radius = float(request.query_params.get('radius', 5000))

        if not latitude or not longitude:
            return Response({'error': 'latitude and longitude are required'}, status=status.HTTP_400_BAD_REQUEST)

        point = Point(float(longitude), float(latitude))
        vehicles = Vehicle.objects.filter(
            last_location__distance_lte=(point, D(m=radius)),
            is_active=True
        ).distance(point).order_by('distance')

        serializer = VehicleListSerializer(vehicles, many=True)
        return Response(serializer.data)


class LocationHistoryViewSet(viewsets.ModelViewSet):
    queryset = LocationHistory.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return LocationHistoryCreateSerializer
        return LocationHistorySerializer

    def get_queryset(self):
        queryset = LocationHistory.objects.select_related('vehicle')
        vehicle_id = self.request.query_params.get('vehicle', None)
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)

        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        location = serializer.save()

        vehicle = location.vehicle
        geofences = Geofence.objects.filter(
            organization=vehicle.organization,
            is_active=True
        )

        for geofence in geofences:
            if geofence.contains_point(location.location):
                recent_alert = GeofenceAlert.objects.filter(
                    vehicle=vehicle,
                    geofence=geofence,
                    alert_type='entry',
                    timestamp__gte=timezone.now() - timedelta(minutes=5)
                ).exists()

                if not recent_alert:
                    GeofenceAlert.objects.create(
                        geofence=geofence,
                        vehicle=vehicle,
                        alert_type='entry',
                        location=location.location
                    )

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TripDetailSerializer
        return TripSerializer

    def get_queryset(self):
        queryset = Trip.objects.select_related('vehicle', 'driver__user')
        vehicle_id = self.request.query_params.get('vehicle', None)
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)

        driver_id = self.request.query_params.get('driver', None)
        if driver_id:
            queryset = queryset.filter(driver_id=driver_id)

        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        trip = self.get_object()
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')

        if not latitude or not longitude:
            return Response({'error': 'latitude and longitude are required'}, status=status.HTTP_400_BAD_REQUEST)

        end_location = Point(float(longitude), float(latitude))
        trip.complete_trip(end_location)

        serializer = self.get_serializer(trip)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        trip = self.get_object()
        trip.status = 'cancelled'
        trip.save()
        return Response({'detail': 'Trip cancelled'})


class GeofenceViewSet(viewsets.ModelViewSet):
    queryset = Geofence.objects.all()
    serializer_class = GeofenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Geofence.objects.all()
        organization_id = self.request.query_params.get('organization', None)
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        return queryset

    @action(detail=True, methods=['get'])
    def vehicles_inside(self, request, pk=None):
        geofence = self.get_object()
        vehicles_inside = []

        vehicles = Vehicle.objects.filter(
            organization=geofence.organization,
            is_active=True,
            last_location__isnull=False
        )

        for vehicle in vehicles:
            if geofence.contains_point(vehicle.last_location):
                vehicles_inside.append(vehicle)

        serializer = VehicleListSerializer(vehicles_inside, many=True)
        return Response(serializer.data)


class GeofenceAlertViewSet(viewsets.ModelViewSet):
    queryset = GeofenceAlert.objects.all()
    serializer_class = GeofenceAlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = GeofenceAlert.objects.select_related('vehicle', 'geofence', 'acknowledged_by')
        vehicle_id = self.request.query_params.get('vehicle', None)
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)

        acknowledged = self.request.query_params.get('acknowledged', None)
        if acknowledged:
            queryset = queryset.filter(acknowledged=acknowledged.lower() == 'true')

        return queryset

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        alert.acknowledged = True
        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = request.user
        alert.save()
        return Response({'detail': 'Alert acknowledged'})


class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceRecord.objects.all()
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = MaintenanceRecord.objects.select_related('vehicle')
        vehicle_id = self.request.query_params.get('vehicle', None)
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)

        maintenance_type = self.request.query_params.get('type', None)
        if maintenance_type:
            queryset = queryset.filter(maintenance_type=maintenance_type)

        return queryset

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date() + timedelta(days=days)

        upcoming = MaintenanceRecord.objects.filter(
            next_service_date__lte=end_date,
            next_service_date__gte=timezone.now().date()
        ).order_by('next_service_date')

        serializer = self.get_serializer(upcoming, many=True)
        return Response(serializer.data)