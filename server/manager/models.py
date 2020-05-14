from django.db import models
from django.utils import timezone


class Task(models.Model):
    name = models.CharField(max_length=60)
    description = models.CharField(max_length=400)
    command = models.CharField(max_length=100)

    period = models.DurationField()
    last_completed_time = models.DateTimeField()

    @property
    def next_scheduled_time(self):
        return self.last_completed_time + self.period
    
    def is_overdue(self):
        return self.next_scheduled_time < timezone.now()

    def __str__(self):
        return f'{self.name}'


class SensorReading(models.Model):
    sensor = models.ForeignKey('Sensor', on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=5, decimal_places=3)
    time = models.DateTimeField()

    def __str__(self):
        return f'{self.sensor} {self.time}'


class Sensor(models.Model):
    name = models.CharField(max_length=60)

    @property
    def latest_reading(self):
        return SensorReading.objects.filter(sensor=self.id).latest('time')
    
    def __str__(self):
        return f'{self.name}'


class Plant(models.Model):
    name = models.CharField(max_length=60)
    # associated tasks and sensors
    tasks = models.ManyToManyField(Task)
    sensors = models.ManyToManyField(Sensor)

    def get_tasks(self):
        return self.tasks.order_by('name')

    def get_sensors(self):
        return self.sensors.order_by('name')

    def __str__(self):
        return f'{self.name}'
