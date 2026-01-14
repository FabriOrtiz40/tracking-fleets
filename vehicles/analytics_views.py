from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Avg, Sum, Max, Min, F, Q
from django.db.models.functions import TruncDate, TruncHour
from django.utils import timezone
from datetime import timedelta

from .models import Vehicle, Trip, LocationHistory, Organization, Driver, MaintenanceRecord


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fleet_overview(request):
    organization_id = request.query_params.get('organization')

    if not organization_id:
        return Response({'error': 'organization parameter is required'}, status=400)

    vehicles = Vehicle.objects.filter(organization_id=organization_id, is_active=True)

    total_vehicles = vehicles.count()
    active_vehicles = sum(1 for v in vehicles if v.is_moving())
    idle_vehicles = total_vehicles - active_vehicles
    maintenance_vehicles = vehicles.filter(status='maintenance').count()

    trips_today = Trip.objects.filter(
        vehicle__organization_id=organization_id,
        start_time__date=timezone.now().date()
    )

    return Response({
        'total_vehicles': total_vehicles,
        'active_vehicles': active_vehicles,
        'idle_vehicles': idle_vehicles,
        'maintenance_vehicles': maintenance_vehicles,
        'trips_today': trips_today.count(),
        'distance_today': trips_today.aggregate(Sum('distance'))['distance__sum'] or 0,
        'avg_fuel_level': vehicles.aggregate(Avg('fuel_level'))['fuel_level__avg'] or 0,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vehicle_utilization(request):
    organization_id = request.query_params.get('organization')
    days = int(request.query_params.get('days', 7))

    if not organization_id:
        return Response({'error': 'organization parameter is required'}, status=400)

    start_date = timezone.now() - timedelta(days=days)

    vehicles = Vehicle.objects.filter(organization_id=organization_id, is_active=True)

    utilization_data = []
    for vehicle in vehicles:
        trips = Trip.objects.filter(
            vehicle=vehicle,
            start_time__gte=start_date,
            status='completed'
        )

        total_trips = trips.count()
        total_distance = trips.aggregate(Sum('distance'))['distance__sum'] or 0
        total_duration = sum((t.duration.total_seconds() / 3600 for t in trips if t.duration), 0)

        utilization_data.append({
            'vehicle_id': vehicle.id,
            'plate': vehicle.plate,
            'type': vehicle.type,
            'total_trips': total_trips,
            'total_distance': round(total_distance, 2),
            'total_hours': round(total_duration, 2),
            'utilization_rate': round((total_duration / (days * 24)) * 100, 2) if days > 0 else 0
        })

    return Response({
        'period_days': days,
        'vehicles': utilization_data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_performance(request):
    organization_id = request.query_params.get('organization')
    days = int(request.query_params.get('days', 30))

    if not organization_id:
        return Response({'error': 'organization parameter is required'}, status=400)

    start_date = timezone.now() - timedelta(days=days)

    drivers = Driver.objects.filter(organization_id=organization_id)

    performance_data = []
    for driver in drivers:
        trips = Trip.objects.filter(
            driver=driver,
            start_time__gte=start_date,
            status='completed'
        )

        total_trips = trips.count()
        total_distance = trips.aggregate(Sum('distance'))['distance__sum'] or 0
        avg_speed = trips.aggregate(Avg('avg_speed'))['avg_speed__avg'] or 0
        max_speed_recorded = trips.aggregate(Max('max_speed'))['max_speed__max'] or 0

        performance_data.append({
            'driver_id': driver.id,
            'name': driver.user.get_full_name(),
            'license': driver.license_number,
            'total_trips': total_trips,
            'total_distance': round(total_distance, 2),
            'average_speed': round(avg_speed, 2),
            'max_speed': round(max_speed_recorded, 2),
            'trips_per_day': round(total_trips / days, 2) if days > 0 else 0
        })

    return Response({
        'period_days': days,
        'drivers': performance_data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trip_analytics(request):
    organization_id = request.query_params.get('organization')
    days = int(request.query_params.get('days', 30))

    if not organization_id:
        return Response({'error': 'organization parameter is required'}, status=400)

    start_date = timezone.now() - timedelta(days=days)

    trips = Trip.objects.filter(
        vehicle__organization_id=organization_id,
        start_time__gte=start_date,
        status='completed'
    )

    daily_stats = trips.annotate(
        date=TruncDate('start_time')
    ).values('date').annotate(
        trip_count=Count('id'),
        total_distance=Sum('distance'),
        avg_speed=Avg('avg_speed')
    ).order_by('date')

    return Response({
        'period_days': days,
        'total_trips': trips.count(),
        'total_distance': trips.aggregate(Sum('distance'))['distance__sum'] or 0,
        'average_distance': trips.aggregate(Avg('distance'))['distance__avg'] or 0,
        'average_speed': trips.aggregate(Avg('avg_speed'))['avg_speed__avg'] or 0,
        'daily_breakdown': list(daily_stats)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def maintenance_analytics(request):
    organization_id = request.query_params.get('organization')

    if not organization_id:
        return Response({'error': 'organization parameter is required'}, status=400)

    vehicles = Vehicle.objects.filter(organization_id=organization_id)

    maintenance_records = MaintenanceRecord.objects.filter(
        vehicle__organization_id=organization_id
    )

    total_maintenance_cost = maintenance_records.aggregate(Sum('cost'))['cost__sum'] or 0

    maintenance_by_type = maintenance_records.values('maintenance_type').annotate(
        count=Count('id'),
        total_cost=Sum('cost')
    ).order_by('-count')

    upcoming_maintenance = MaintenanceRecord.objects.filter(
        vehicle__organization_id=organization_id,
        next_service_date__isnull=False,
        next_service_date__gte=timezone.now().date()
    ).order_by('next_service_date')[:10]

    overdue_maintenance = MaintenanceRecord.objects.filter(
        vehicle__organization_id=organization_id,
        next_service_date__isnull=False,
        next_service_date__lt=timezone.now().date()
    ).count()

    from .serializers import MaintenanceRecordSerializer

    return Response({
        'total_maintenance_records': maintenance_records.count(),
        'total_cost': float(total_maintenance_cost),
        'average_cost_per_vehicle': float(total_maintenance_cost / vehicles.count()) if vehicles.count() > 0 else 0,
        'overdue_count': overdue_maintenance,
        'maintenance_by_type': list(maintenance_by_type),
        'upcoming_maintenance': MaintenanceRecordSerializer(upcoming_maintenance, many=True).data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def speed_violations(request):
    organization_id = request.query_params.get('organization')
    days = int(request.query_params.get('days', 7))
    speed_limit = float(request.query_params.get('speed_limit', 120))

    if not organization_id:
        return Response({'error': 'organization parameter is required'}, status=400)

    start_date = timezone.now() - timedelta(days=days)

    violations = LocationHistory.objects.filter(
        vehicle__organization_id=organization_id,
        timestamp__gte=start_date,
        speed__gt=speed_limit
    ).select_related('vehicle')

    violations_by_vehicle = violations.values(
        'vehicle__id', 'vehicle__plate'
    ).annotate(
        violation_count=Count('id'),
        max_speed=Max('speed'),
        avg_speed=Avg('speed')
    ).order_by('-violation_count')

    return Response({
        'period_days': days,
        'speed_limit': speed_limit,
        'total_violations': violations.count(),
        'violations_by_vehicle': list(violations_by_vehicle)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fuel_consumption(request):
    organization_id = request.query_params.get('organization')
    days = int(request.query_params.get('days', 30))

    if not organization_id:
        return Response({'error': 'organization parameter is required'}, status=400)

    start_date = timezone.now() - timedelta(days=days)

    vehicles = Vehicle.objects.filter(organization_id=organization_id, is_active=True)

    fuel_data = []
    for vehicle in vehicles:
        trips = Trip.objects.filter(
            vehicle=vehicle,
            start_time__gte=start_date,
            status='completed'
        )

        total_distance = trips.aggregate(Sum('distance'))['distance__sum'] or 0
        total_fuel = trips.aggregate(Sum('fuel_consumed'))['fuel_consumed__sum'] or 0

        fuel_efficiency = (total_distance / total_fuel) if total_fuel > 0 else 0

        fuel_data.append({
            'vehicle_id': vehicle.id,
            'plate': vehicle.plate,
            'type': vehicle.type,
            'total_distance': round(total_distance, 2),
            'total_fuel_consumed': round(total_fuel, 2),
            'fuel_efficiency_km_per_liter': round(fuel_efficiency, 2),
            'current_fuel_level': vehicle.fuel_level
        })

    return Response({
        'period_days': days,
        'vehicles': fuel_data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def geofence_report(request):
    organization_id = request.query_params.get('organization')
    days = int(request.query_params.get('days', 7))

    if not organization_id:
        return Response({'error': 'organization parameter is required'}, status=400)

    start_date = timezone.now() - timedelta(days=days)

    from .models import GeofenceAlert

    alerts = GeofenceAlert.objects.filter(
        geofence__organization_id=organization_id,
        timestamp__gte=start_date
    )

    alerts_by_geofence = alerts.values(
        'geofence__id', 'geofence__name', 'alert_type'
    ).annotate(
        count=Count('id')
    ).order_by('-count')

    alerts_by_vehicle = alerts.values(
        'vehicle__id', 'vehicle__plate'
    ).annotate(
        count=Count('id')
    ).order_by('-count')

    unacknowledged_alerts = alerts.filter(acknowledged=False).count()

    return Response({
        'period_days': days,
        'total_alerts': alerts.count(),
        'unacknowledged_alerts': unacknowledged_alerts,
        'alerts_by_geofence': list(alerts_by_geofence),
        'alerts_by_vehicle': list(alerts_by_vehicle)
    })
