# Fleet Tracking System

Sistema genérico de localización y gestión de flotas para camiones, delivery, taxis o cualquier tipo de vehículo.

## Características Principales

### Gestión de Flotas
- **Organizaciones**: Soporte multi-organización para gestionar múltiples flotas
- **Vehículos**: Registro completo de vehículos con tracking en tiempo real
- **Conductores**: Gestión de conductores y asignación a vehículos
- **Tracking GPS**: Historial completo de ubicaciones con timestamps

### Funcionalidades de Tracking
- Ubicación en tiempo real de todos los vehículos
- Historial de rutas y trayectorias
- Velocidad actual y promedio
- Estado del motor (encendido/apagado)
- Nivel de combustible y batería
- Odómetro digital

### Viajes (Trips)
- Registro automático de viajes
- Cálculo de distancia recorrida
- Estadísticas de velocidad (máxima y promedio)
- Consumo de combustible
- Duración y métricas del viaje

### Geofencing
- Creación de geocercas (círculos o polígonos)
- Alertas automáticas de entrada/salida
- Monitoreo de vehículos dentro de zonas
- Historial de alertas

### Mantenimiento
- Registro de mantenimientos realizados
- Programación de servicios futuros
- Alertas de mantenimiento pendiente
- Historial de costos

### Analytics y Reportes
- Vista general de la flota (dashboard)
- Utilización de vehículos
- Rendimiento de conductores
- Análisis de viajes
- Consumo de combustible
- Violaciones de velocidad
- Reportes de geocercas

## Tecnologías Utilizadas

- **Django 5.0.6**: Framework web
- **Django REST Framework**: API REST
- **Django GIS (GeoDjango)**: Funcionalidades geoespaciales
- **PostgreSQL + PostGIS**: Base de datos con soporte geoespacial (o SQLite para desarrollo)
- **Django CORS Headers**: Soporte para aplicaciones frontend separadas

## Instalación

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd tracking-fleets
```

### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos

Para desarrollo con SQLite (incluido en Django):
```python
# settings.py ya está configurado para SQLite por defecto
```

Para producción con PostgreSQL + PostGIS:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'fleet_tracking',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 5. Ejecutar migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crear superusuario
```bash
python manage.py createsuperuser
```

### 7. Ejecutar servidor
```bash
python manage.py runserver
```

## Endpoints de la API

### Autenticación
- `POST /api-auth/login/` - Login
- `POST /api-auth/logout/` - Logout
- Token Authentication también disponible

### Organizaciones
- `GET /api/organizations/` - Listar organizaciones
- `POST /api/organizations/` - Crear organización
- `GET /api/organizations/{id}/` - Detalle de organización
- `GET /api/organizations/{id}/dashboard/` - Dashboard de organización

### Conductores (Drivers)
- `GET /api/drivers/` - Listar conductores
- `POST /api/drivers/` - Crear conductor
- `GET /api/drivers/{id}/` - Detalle de conductor
- `GET /api/drivers/{id}/stats/` - Estadísticas del conductor

### Vehículos
- `GET /api/vehicles/` - Listar vehículos
- `POST /api/vehicles/` - Registrar vehículo
- `GET /api/vehicles/{id}/` - Detalle de vehículo
- `GET /api/vehicles/{id}/current_location/` - Ubicación actual
- `GET /api/vehicles/{id}/location_history/?hours=24` - Historial de ubicaciones
- `POST /api/vehicles/{id}/assign_driver/` - Asignar conductor
- `POST /api/vehicles/{id}/remove_driver/` - Remover conductor
- `GET /api/vehicles/nearby/?latitude=X&longitude=Y&radius=5000` - Vehículos cercanos

### Ubicaciones (Location History)
- `GET /api/locations/` - Listar ubicaciones
- `POST /api/locations/` - Registrar nueva ubicación (tracking)

Ejemplo de POST para tracking:
```json
{
  "vehicle": 1,
  "latitude": -34.603722,
  "longitude": -58.381592,
  "speed": 60.5,
  "heading": 180,
  "timestamp": "2024-06-15T10:30:00Z",
  "battery_level": 85.0,
  "is_ignition_on": true
}
```

### Viajes (Trips)
- `GET /api/trips/` - Listar viajes
- `POST /api/trips/` - Iniciar viaje
- `GET /api/trips/{id}/` - Detalle del viaje
- `POST /api/trips/{id}/complete/` - Finalizar viaje
- `POST /api/trips/{id}/cancel/` - Cancelar viaje

### Geocercas (Geofences)
- `GET /api/geofences/` - Listar geocercas
- `POST /api/geofences/` - Crear geocerca
- `GET /api/geofences/{id}/vehicles_inside/` - Vehículos dentro de la geocerca

### Alertas
- `GET /api/alerts/` - Listar alertas
- `POST /api/alerts/{id}/acknowledge/` - Reconocer alerta

### Mantenimiento
- `GET /api/maintenance/` - Listar registros de mantenimiento
- `POST /api/maintenance/` - Crear registro
- `GET /api/maintenance/upcoming/?days=30` - Mantenimientos próximos

### Analytics
- `GET /api/analytics/fleet-overview/?organization=1` - Vista general
- `GET /api/analytics/vehicle-utilization/?organization=1&days=7` - Utilización
- `GET /api/analytics/driver-performance/?organization=1&days=30` - Rendimiento
- `GET /api/analytics/trip-analytics/?organization=1&days=30` - Análisis de viajes
- `GET /api/analytics/maintenance-analytics/?organization=1` - Análisis de mantenimiento
- `GET /api/analytics/speed-violations/?organization=1&speed_limit=120` - Violaciones
- `GET /api/analytics/fuel-consumption/?organization=1&days=30` - Consumo
- `GET /api/analytics/geofence-report/?organization=1&days=7` - Reporte de geocercas

## Modelos de Datos

### Organization
Representa una empresa u organización que gestiona una flota.

### Driver
Conductores asociados a una organización.

### Vehicle
Vehículos con información completa y ubicación en tiempo real.

### LocationHistory
Historial de ubicaciones GPS de cada vehículo.

### Trip
Viajes realizados por vehículos con métricas completas.

### Geofence
Geocercas para monitoreo de zonas.

### GeofenceAlert
Alertas generadas al entrar/salir de geocercas.

### MaintenanceRecord
Registros de mantenimiento de vehículos.

## Panel de Administración

Accede al panel de administración en `/admin/` con el superusuario creado.

El panel incluye:
- Gestión completa de todos los modelos
- Visualización de mapas (GIS)
- Filtros avanzados
- Búsqueda por múltiples campos
- Interfaz organizada con fieldsets

## Uso del Sistema

### 1. Configuración inicial
1. Crear una organización desde el admin o API
2. Crear usuarios y conductores
3. Registrar vehículos

### 2. Tracking en tiempo real
Enviar ubicaciones periódicamente desde dispositivos GPS:
```python
POST /api/locations/
{
  "vehicle": 1,
  "latitude": -34.603722,
  "longitude": -58.381592,
  "speed": 60.5,
  "timestamp": "2024-06-15T10:30:00Z"
}
```

### 3. Gestión de viajes
```python
# Iniciar viaje
POST /api/trips/
{
  "vehicle": 1,
  "driver": 1,
  "start_location": {
    "type": "Point",
    "coordinates": [-58.381592, -34.603722]
  }
}

# Finalizar viaje
POST /api/trips/1/complete/
{
  "latitude": -34.615,
  "longitude": -58.395
}
```

### 4. Monitoreo
- Ver dashboard de organización
- Consultar vehículos activos
- Revisar alertas de geocercas
- Generar reportes analíticos

## Próximas Funcionalidades

- WebSocket para tracking en tiempo real
- Notificaciones push
- Reportes PDF exportables
- Integración con Waze/Google Maps
- App móvil para conductores
- Alertas por email/SMS
- Dashboard interactivo con gráficos

## Licencia

MIT
