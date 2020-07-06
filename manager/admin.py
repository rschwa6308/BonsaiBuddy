from django.contrib import admin
from .models import Task, Sensor, SensorReading, Plant

admin.site.register(Task)
admin.site.register(Sensor)
admin.site.register(SensorReading)
admin.site.register(Plant)