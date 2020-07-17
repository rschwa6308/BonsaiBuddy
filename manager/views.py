from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import json
from datetime import datetime, timedelta
import logging, os

from .models import Task, Sensor, SensorReading, Plant



# Get an instance of a named logger
logger = logging.getLogger('tasks')


# The longest the client can be silent for and still be considered 'OK'
CLIENT_SILENCE_PERIOD = timedelta(hours=1)

def home(request):
    try:
        last_update_time = SensorReading.objects.latest('time').time
        client_ok = datetime.now() - last_update_time < CLIENT_SILENCE_PERIOD
    except SensorReading.DoesNotExist:
        last_update_time = None #datetime(year=1, month=1, day=1)
        client_ok = False
    
    return render(
        request,
        'manager/home.html',
        {
            'last_update_time': last_update_time,
            'client_ok': client_ok,
        }
    )


def task_list(request):
    tasks = list(Task.objects.all())
    tasks.sort(key=lambda t: t.next_scheduled_time)
    return render(
        request,
        'manager/task_list.html',
        {'tasks': tasks}
    )


def task_details(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    return render(
        request,
        'manager/task_details.html',
        {'task': task}
    )


def sensor_list(request):
    sensors = Sensor.objects.order_by('name')
    return render(
        request,
        'manager/sensor_list.html',
        {'sensors': sensors}
    )


def sensor_data(request, sensor_id):
    readings = SensorReading.objects.filter(sensor=sensor_id).all()
    data = [{
        'x': reading.time.timestamp(),
        'y': float(reading.value)
    } for reading in readings]
    data.sort(key=lambda item: item['x'])
    return JsonResponse({
        'data': data
    })


# maximum number of categories 
MAX_CATEGORIES = 100

def sensor_details(request, sensor_id):
    sensor = get_object_or_404(Sensor, pk=sensor_id)
    return render(
        request,
        'manager/sensor_details.html',
        {'sensor': sensor}
    )


def plant_list(request):
    plants = Plant.objects.order_by('name')
    return render(
        request,
        'manager/plant_list.html',
        {'plants': plants}
    )


def plant_details(request, plant_id):
    plant = get_object_or_404(Plant, pk=plant_id)
    return render(
        request,
        'manager/plant_details.html',
        {'plant': plant}
    )


def next_tasks(request):
    tasks = [{
        'task_id': task.id,
        'command': task.command,
        'next_time': task.next_scheduled_time.timestamp()
    } for task in Task.objects.filter(enabled=True)]
    return JsonResponse({
        'scheduled_tasks': tasks
    })


UPLOAD_PASSWORD = os.environ.get('UPLOAD_PASSWORD')     # provided by heroku Config Vars

@csrf_exempt
def sensor_update(request):
    if request.method != 'POST':
        return HttpResponse()

    try:
        content = json.loads(request.body)
        if content['password'] != UPLOAD_PASSWORD:
            return HttpResponse(status=403)

        new_readings = [
            SensorReading(
                sensor=Sensor.objects.get(name=s['sensor_name']),
                value=s['value'],
                time=datetime.fromtimestamp(s['time'])
            ) for s in content['sensors']
        ]

        for new_reading in new_readings:
            new_reading.save()

        return HttpResponse()
    except Exception as e:
        return HttpResponse(status=500)


@csrf_exempt
def notify_task_completed(request):
    if request.method != 'POST':
        return HttpResponse()

    try:
        content = json.loads(request.body)
        if content['password'] != UPLOAD_PASSWORD:
            return HttpResponse(status=403)
        
        task = Task.objects.get(pk=content['task_id'])
        task.last_completed_time = datetime.fromtimestamp(content['completion_time'])
        task.save()
        # print(f'Task updated!!! ({task})')
        logger.info(f'Task #{task.id} (\"{task.name}\") completed at {task.last_completed_time}')

        return HttpResponse()
    except Exception as e:
        print(e)
        return HttpResponse(status=500)


TASKS_LOG_FILENAME = os.path.join(settings.LOGS_DIR, 'tasks.log')
def task_history(request):
    task_logs = []
    if os.path.isfile(TASKS_LOG_FILENAME):
        with open(TASKS_LOG_FILENAME, 'r') as f:
            task_logs += f.read().split('\n')
    
    # strip off log timestamps, exclude empty strings, and reverse order
    task_logs = [l[32:] for l in task_logs if l][::-1]
    return render(
        request,
        'manager/task_history.html',
        {'task_logs': task_logs}
    )
