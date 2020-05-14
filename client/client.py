import requests
from requests.compat import urljoin
import json
import threading, time, logging
from random import random
import signal



# set logging output format
logging.basicConfig(level=logging.INFO, format='%(threadName)s (%(thread)s):\t%(message)s')


# minium amount of time between event executions (seconds)
EVENT_EXECUTION_PERIOD = 10

# amount of time between GET/POST requests (seconds)
BATCH_UPDATE_PERIOD = 10 * 60   # every 10 minutes


BASE_URL = 'http://localhost:8000/'
TASKS_UPDATE_URL = urljoin(BASE_URL, 'next_tasks/')
SENSOR_UPDATE_URL = urljoin(BASE_URL, 'sensor_update/')
TASK_NOTIFICATION_URL = urljoin(BASE_URL, 'notify_task/')
UPLOAD_PASSWORD = 'password'


class Client:
    def __init__(self):
        self.quit_event = threading.Event()
        self.tasks_worker = None
        self.status_updates_worker = None
        self.execution_lock = threading.RLock()

        self.scheduled_tasks = {}

    # execute the given command; return an error message if execution fails
    def execute_command(self, command):
        logging.info(f'Executing command: {command}... ')
        time.sleep(10)
        error_message = None
        if error_message is None:
            logging.info('Command executed successfully')
        else:
            logging.error(f'Command failed with error message: {error_message}')
        return error_message
    
    # download the next tasks from the server
    def get_tasks_update(self):
        logging.info('Checking for task updates...')
        response = requests.get(TASKS_UPDATE_URL)
        if response.ok:
            logging.info(f'Update downloaded successfully')
        else:
            logging.error(f'Failed to download update with status code: {response.status_code} ({response.reason})')
        return json.loads(response.content)
    
    def post_sensor_update(self):
        logging.info('Reading sensor values... ')
        status_update = {
            'password': UPLOAD_PASSWORD,
            'sensors': [
                {
                    'sensor_name': 'test sensor',
                    'value': random(),
                    'time': round(time.time()),
                },
                {
                    'sensor_name': 'test sensor 2',
                    'value': random(),
                    'time': round(time.time()),
                }
            ]
        }
        logging.info('Done')

        logging.info('Posting sensor update... ')
        response = requests.post(SENSOR_UPDATE_URL, json=status_update)
        if response.ok:
            logging.info('Sensor update posted successfully')
        else:
            logging.error(f'Failed to post sensor update with status code: {response.status_code} ({response.reason})')
    
    def notify_task_completed(self, task):
        logging.info('Posting task completion notification... ')
        status_update = {
            'password': UPLOAD_PASSWORD,
            'task_id': task['task_id'],
            'completion_time': round(time.time())   # TODO: fix internal server error with this response body
        }
        requests.post(TASK_NOTIFICATION_URL, json=status_update)
        logging.info('Done')

    def _run_tasks(self):
        time.sleep(1)   # allow self.start() to finish gracefully
        while not self.quit_event.is_set():
            current_time = time.time()
            for task in self.scheduled_tasks:
                if task['next_time'] <= current_time:
                    logging.info(f'Queuing task #{task["task_id"]}')
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
                    logging.info(f'New tasks found: {new_tasks}')
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
        logging.info(f'Client started with worker threads "{self.tasks_worker.name}" ({self.tasks_worker.ident}) and "{self.status_updates_worker.name}" ({self.status_updates_worker.ident})')
    
    def stop(self):
        logging.info('Stopping all workers...')
        self.quit_event.set()
        self.tasks_worker.join()
        self.status_updates_worker.join()
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
