
from django.contrib.gis.db import models

class Vehicle(models.Model):
    TYPES = [
        ('car', 'Car'),
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('taxi', 'Taxi'),
        ('moto', 'Moto'),
    ]
    plate = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=10, choices=TYPES)
    last_location = models.PointField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    fuel_level = models.FloatField(default=100.0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.type} - {self.plate}"
    
class Trip(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    start_location = models.PointField()
    end_location = models.PointField(null=True, blank=True)
    distance = models.FloatField(null=True, blank=True)  # en km

    def __str__(self):
        return f"Trip {self.id} - {self.vehicle.plate}"