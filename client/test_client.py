import requests, json
import datetime
import time


UPLOAD_PASSWORD = 'password'

# data = {
#     'password': UPLOAD_PASSWORD,
#     'sensors': [
#         {
#             'sensor_name': 'test sensor',
#             'value': 0.696,
#             'time': round(datetime.datetime.today().timestamp()),
#         },
#         {
#             'sensor_name': 'test sensor 2',
#             'value': 0.123,
#             'time': round(datetime.datetime.today().timestamp()),
#         }
#     ]
# }
# response = requests.post('http://127.0.0.1:8000/sensor_update/', json=data)


data = {
    'password': UPLOAD_PASSWORD,
    'task_id': 1,
    'completion_time': round(time.time())
}
response = requests.post('http://localhost:8000/notify_task/', json=data)
