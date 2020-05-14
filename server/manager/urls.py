from django.urls import path

from . import views

urlpatterns = [ 
    path('', views.home, name='home'),
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/<int:task_id>/', views.task_details, name='task_details'),
    path('sensors/', views.sensor_list, name='sensor_list'),
    path('sensors/<int:sensor_id>/', views.sensor_details, name='sensor_details'),
    path('sensors/<int:sensor_id>/data/', views.sensor_data, name='sensor_data'),
    path('plants/', views.plant_list, name='plant_list'),
    path('plants/<int:plant_id>', views.plant_details, name='plant_details'),
    path('next_tasks/', views.next_tasks, name='next_tasks'),
    path('sensor_update/', views.sensor_update, name='sensor_update'),
    path('notify_task/', views.notify_task_completed, name='notify_task'),
    path('task_history/', views.task_history, name='task_history'),
]