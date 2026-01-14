from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from math import radians, cos, sin, asin, sqrt


class Organization(models.Model):
    name = models.CharField(max_length=200)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='drivers')
    license_number = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=20)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.license_number}"

    class Meta:
        ordering = ['user__first_name', 'user__last_name']


class Vehicle(models.Model):
    TYPES = [
        ('car', 'Car'),
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('taxi', 'Taxi'),
        ('moto', 'Moto'),
        ('bus', 'Bus'),
        ('delivery', 'Delivery'),
    ]

    STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Maintenance'),
        ('out_of_service', 'Out of Service'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='vehicles')
    plate = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=10, choices=TYPES)
    brand = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    year = models.IntegerField(null=True, blank=True)
    vin = models.CharField(max_length=17, blank=True, help_text='Vehicle Identification Number')

    # Ubicación usando coordenadas simples
    last_latitude = models.FloatField(null=True, blank=True, help_text='Last known latitude')
    last_longitude = models.FloatField(null=True, blank=True, help_text='Last known longitude')
    last_updated = models.DateTimeField(auto_now=True)

    current_driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_vehicle')

    fuel_level = models.FloatField(default=100.0, help_text='Fuel level in percentage')
    odometer = models.FloatField(default=0.0, help_text='Odometer reading in km')

    status = models.CharField(max_length=20, choices=STATUS, default='active')
    is_active = models.BooleanField(default=True)

    max_speed = models.FloatField(null=True, blank=True, help_text='Maximum allowed speed in km/h')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.plate} - {self.get_type_display()}"

    def get_current_speed(self):
        latest = self.location_history.order_by('-timestamp').first()
        return latest.speed if latest else 0

    def is_moving(self):
        return self.get_current_speed() > 0

    class Meta:
        ordering = ['plate']
        indexes = [
            models.Index(fields=['last_latitude', 'last_longitude']),
        ]


class LocationHistory(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='location_history')
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    speed = models.FloatField(default=0.0, help_text='Speed in km/h')
    heading = models.FloatField(null=True, blank=True, help_text='Direction in degrees (0-360)')
    altitude = models.FloatField(null=True, blank=True, help_text='Altitude in meters')
    accuracy = models.FloatField(null=True, blank=True, help_text='GPS accuracy in meters')

    battery_level = models.FloatField(null=True, blank=True)
    is_ignition_on = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.vehicle.plate} - {self.timestamp}"

    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees)
        Returns distance in kilometers
        """
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['vehicle', '-timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['latitude', 'longitude']),
        ]


class Trip(models.Model):
    TRIP_STATUS = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='trips')
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='trips')

    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)

    # Ubicaciones de inicio y fin
    start_latitude = models.FloatField()
    start_longitude = models.FloatField()
    end_latitude = models.FloatField(null=True, blank=True)
    end_longitude = models.FloatField(null=True, blank=True)

    distance = models.FloatField(null=True, blank=True, help_text='Total distance in km')
    duration = models.DurationField(null=True, blank=True)

    max_speed = models.FloatField(null=True, blank=True, help_text='Maximum speed during trip in km/h')
    avg_speed = models.FloatField(null=True, blank=True, help_text='Average speed in km/h')

    fuel_consumed = models.FloatField(null=True, blank=True, help_text='Fuel consumed in liters')

    status = models.CharField(max_length=20, choices=TRIP_STATUS, default='in_progress')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Trip {self.id} - {self.vehicle.plate}"

    def complete_trip(self, end_latitude, end_longitude):
        self.end_time = timezone.now()
        self.end_latitude = end_latitude
        self.end_longitude = end_longitude
        self.duration = self.end_time - self.start_time
        self.status = 'completed'
        self.calculate_stats()
        self.save()

    def calculate_stats(self):
        locations = LocationHistory.objects.filter(
            vehicle=self.vehicle,
            timestamp__gte=self.start_time,
            timestamp__lte=self.end_time
        ).order_by('timestamp')

        if locations.exists():
            speeds = [loc.speed for loc in locations if loc.speed]
            self.max_speed = max(speeds) if speeds else 0
            self.avg_speed = sum(speeds) / len(speeds) if speeds else 0

            total_distance = 0
            prev_loc = None
            for loc in locations:
                if prev_loc:
                    total_distance += LocationHistory.haversine_distance(
                        prev_loc.latitude, prev_loc.longitude,
                        loc.latitude, loc.longitude
                    )
                prev_loc = loc
            self.distance = total_distance

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['vehicle', '-start_time']),
            models.Index(fields=['driver', '-start_time']),
        ]


class Geofence(models.Model):
    GEOFENCE_TYPES = [
        ('circle', 'Circle'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='geofences')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    geofence_type = models.CharField(max_length=10, choices=GEOFENCE_TYPES, default='circle')

    # Solo soportamos círculos por ahora
    center_latitude = models.FloatField(help_text='Center latitude for circle geofence')
    center_longitude = models.FloatField(help_text='Center longitude for circle geofence')
    radius = models.FloatField(help_text='Radius in meters for circle geofence')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def contains_point(self, latitude, longitude):
        """Check if a point is inside the geofence"""
        if self.geofence_type == 'circle':
            distance_km = LocationHistory.haversine_distance(
                self.center_latitude, self.center_longitude,
                latitude, longitude
            )
            distance_m = distance_km * 1000
            return distance_m <= self.radius
        return False

    class Meta:
        ordering = ['name']


class GeofenceAlert(models.Model):
    ALERT_TYPES = [
        ('entry', 'Entry'),
        ('exit', 'Exit'),
    ]

    geofence = models.ForeignKey(Geofence, on_delete=models.CASCADE, related_name='alerts')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='geofence_alerts')
    alert_type = models.CharField(max_length=10, choices=ALERT_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)
    latitude = models.FloatField()
    longitude = models.FloatField()
    acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.vehicle.plate} - {self.alert_type} - {self.geofence.name}"

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['vehicle', '-timestamp']),
        ]


class MaintenanceRecord(models.Model):
    MAINTENANCE_TYPES = [
        ('oil_change', 'Oil Change'),
        ('tire_rotation', 'Tire Rotation'),
        ('brake_service', 'Brake Service'),
        ('inspection', 'Inspection'),
        ('repair', 'Repair'),
        ('other', 'Other'),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    odometer_reading = models.FloatField(help_text='Odometer reading at maintenance in km')
    performed_at = models.DateTimeField(default=timezone.now)
    performed_by = models.CharField(max_length=200, blank=True)
    next_service_date = models.DateField(null=True, blank=True)
    next_service_odometer = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle.plate} - {self.get_maintenance_type_display()} - {self.performed_at.date()}"

    class Meta:
        ordering = ['-performed_at']
