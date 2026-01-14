from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import analytics_views

router = DefaultRouter()
router.register(r'organizations', views.OrganizationViewSet)
router.register(r'drivers', views.DriverViewSet)
router.register(r'vehicles', views.VehicleViewSet)
router.register(r'trips', views.TripViewSet)
router.register(r'locations', views.LocationHistoryViewSet)
router.register(r'geofences', views.GeofenceViewSet)
router.register(r'alerts', views.GeofenceAlertViewSet)
router.register(r'maintenance', views.MaintenanceRecordViewSet)

urlpatterns = [
    path('', views.api_root, name='api-root'),
    path('', include(router.urls)),

    path('analytics/fleet-overview/', analytics_views.fleet_overview, name='fleet-overview'),
    path('analytics/vehicle-utilization/', analytics_views.vehicle_utilization, name='vehicle-utilization'),
    path('analytics/driver-performance/', analytics_views.driver_performance, name='driver-performance'),
    path('analytics/trip-analytics/', analytics_views.trip_analytics, name='trip-analytics'),
    path('analytics/maintenance-analytics/', analytics_views.maintenance_analytics, name='maintenance-analytics'),
    path('analytics/speed-violations/', analytics_views.speed_violations, name='speed-violations'),
    path('analytics/fuel-consumption/', analytics_views.fuel_consumption, name='fuel-consumption'),
    path('analytics/geofence-report/', analytics_views.geofence_report, name='geofence-report'),
]