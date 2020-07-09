import requests
from requests.compat import urljoin
import json
import threading, time, logging
from random import random
import signal
import re
import os

from hardware_interfacing import read_moisture_sensor, read_light_sensor, pump_volume, cleanup_io


# set logging output format
logging.basicConfig(level=logging.INFO, format='%(threadName)s:\t%(message)s')


# minium amount of time between event executions (seconds)
EVENT_EXECUTION_PERIOD = 30

# amount of time between GET/POST requests (seconds)
BATCH_UPDATE_PERIOD = 60 * 60   # every 60 minutes


BASE_URL = 'https://bonsai-buddy-controller.herokuapp.com/'
TASKS_UPDATE_URL = urljoin(BASE_URL, 'next_tasks/')
SENSOR_UPDATE_URL = urljoin(BASE_URL, 'sensor_update/')
TASK_NOTIFICATION_URL = urljoin(BASE_URL, 'notify_task/')

# UPLOAD_PASSWORD = os.environ.get('UPLOAD_PASSWORD')
from secrets import UPLOAD_PASSWORD


def do_nothing():
    print('Doing nothing!!!')


# TARGET_POS_MAP = {
#     'ROBERTO':      0.4,
#     'TEST_TARGET':  0.7
# }

def pump_volume_with_target_name(volume, target_name):
    # target_pos = TARGET_POS_MAP[target_name.upper()]
    # pump_volume_with_target_pos(int(volume), target_pos)
    pump_volume(volume)


COMMANDS = [
    (r'NOOP', do_nothing),
    (r'pump (\d+)ml to (\w+)', pump_volume_with_target_name)
]


class Client:
    def __init__(self):
        self.quit_event = threading.Event()
        self.tasks_worker = None
        self.status_updates_worker = None
        self.execution_lock = threading.RLock()

        self.scheduled_tasks = {}

    # execute the given command; return an error message if execution fails
    def execute_command(self, command):
        logging.info('Executing command: "%s"... ' % command)
        error_message = None
        matched = False
        for com in COMMANDS:
            pattern, function = com
            match = re.fullmatch(pattern, command)
            if match:
                # print('match found! %s' % str(pattern))
                matched = True
                # call function with captured values as args
                try:
                    function(*match.groups())
                except Exception as e:
                    error_message = str(e)
        
        if not matched:
            error_message = 'command "%s" not recognized' % command
        
        if error_message is None:
            logging.info('Command executed successfully')
        else:
            logging.error('Command failed with error message: %s' % error_message)
        
        return error_message
    
    # download the next tasks from the server
    def get_tasks_update(self):
        logging.info('Checking for task updates...')
        response = requests.get(TASKS_UPDATE_URL)
        if response.ok:
            logging.info('Update downloaded successfully')
        else:
            logging.error('Failed to download update with status code: %s (%s)' % (response.status_code, response.reason))
        return response.json()
    
    def post_sensor_update(self):
        logging.info('Reading sensor values... ')
        status_update = {
            'password': UPLOAD_PASSWORD,
            'sensors': [
                {
                    'sensor_name': 'Roberto Moisture Sensor',
                    'value': read_moisture_sensor(),
                    'time': round(time.time()),
                },
                {
                    'sensor_name': 'Light Sensor',
                    'value': read_light_sensor(),
                    'time': round(time.time()),
                }
            ]
        }
        # print(status_update)
        logging.info('Done')

        logging.info('Posting sensor update... ')
        response = requests.post(SENSOR_UPDATE_URL, json=status_update)
        if response.ok:
            logging.info('Sensor update posted successfully')
        else:
            logging.error('Failed to post sensor update with status code: %s (%s)' % (response.status_code, response.reason))
    
    def notify_task_completed(self, task):
        logging.info('Posting task completion notification... ')
        status_update = {
            'password': UPLOAD_PASSWORD,
            'task_id': task['task_id'],
            'completion_time': round(time.time())   # TODO: fix internal server error with this response body
        }
        response = requests.post(TASK_NOTIFICATION_URL, json=status_update)
        if response.ok:
            logging.info('Task completion notification posted successfully')
        else:
            logging.error('Failed to post task completion notification with status code: %s (%s)' % (response.status_code, response.reason))

    def _run_tasks(self):
        time.sleep(1)   # allow self.start() to finish gracefully
        while not self.quit_event.is_set():
            current_time = time.time()
            for task in self.scheduled_tasks:
                if task['next_time'] <= current_time:
                    logging.info('Queuing task #%s' % {task["task_id"]})
                    with self.execution_lock:
                        self.execute_command(task['command'])
                        self.notify_task_completed(task)
                        self.scheduled_tasks.remove(task)
            self.quit_event.wait(EVENT_EXECUTION_PERIOD)
    
    def _run_updates(self):
        time.sleep(1)   # allow self.start() to finish gracefully
        while not self.quit_event.is_set():
            # GET task updates from server (after waiting for any in-progress commands to finish executing)
            with self.execution_lock:
                new_tasks = self.get_tasks_update()['scheduled_tasks']
                if self.scheduled_tasks == new_tasks:
                    logging.info('No new tasks found')
                else:
                    logging.info('New tasks found: %s' % new_tasks)
                    self.scheduled_tasks = new_tasks
                
            # POST sensor status update to server (after waiting for any in_progress commands to finish executing)
            with self.execution_lock:
                self.post_sensor_update()
            
            self.quit_event.wait(BATCH_UPDATE_PERIOD)
    
    def start(self):
        self.quit_event.clear()
        self.tasks_worker = threading.Thread(target=self._run_tasks, name='TasksWorker', daemon=True)
        self.status_updates_worker = threading.Thread(target=self._run_updates, name='UpdatesWorker', daemon=True)
        self.tasks_worker.start()
        self.status_updates_worker.start()
        logging.info('Client started with worker threads "%s" (%s) and "%s" (%s)' %
                     (self.tasks_worker.name, self.tasks_worker.ident, self.status_updates_worker.name, self.status_updates_worker.ident))
    
    def stop(self):
        logging.info('Stopping all workers...')
        self.quit_event.set()
        self.tasks_worker.join()
        self.status_updates_worker.join()
        cleanup_io()
        logging.info('Done')
    
    def run_forever(self):
        signal.signal(signal.SIGINT, lambda sig, frame: self.stop())
        self.start()
        # keep main thread alive (to receive kill signal)
        while not self.quit_event.is_set():
            time.sleep(1)
        


def main():
    client = Client()
    client.run_forever()

if __name__ == '__main__':
    main()
