from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Vehicle, Trip
from .serializers import VehicleSerializer, TripSerializer

@api_view(['GET'])
def api_root(request):
    return Response({
        'message': 'Bienvenido a la API de Fleet Tracker',
        'vehicles': request.build_absolute_uri('vehicles/'),
        'trips': request.build_absolute_uri('trips/'),
    })

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer