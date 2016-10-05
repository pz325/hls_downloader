import time
import zmq
import uuid
from multiprocessing import Process
from multiprocessing import Lock
from multiprocessing import Manager


GLOBAL_TASKS_LOCK = Lock()
GLOBAL_PRINT_LOCK = Lock()
TASK_PORT = 5000
RESULT_PORT = 5001
WORKER_ACK_PORT = 9000
SINK_ACK_PORT = 9001
CONTEXT = zmq.Context()


class Task(object):
    def __init__(self, task_id, command, status='start'):
        '''
        @param task_id Unique id for a task
        @param command An object
        '''
        self.id = task_id
        self.command = command
        self.status = status

    def set_done(self):
        self.status = 'done'

    def is_done(self):
        return 'done' == self.status

    def __repr__(self):
        return 'task {id}: stauts {status}'.format(id=self.id, status=self.status)


def blocking_print(message):
    GLOBAL_PRINT_LOCK.acquire()
    print(message)
    GLOBAL_PRINT_LOCK.release()


def _update_task_list(task):
    '''
    @param task Task object
    id is uri
    '''
    blocking_print('Update task {task} as {status}'.format(task=task.id, status=task.status))
    TASKS[task.id] = task
    _print_tasks()


def _worker(action):
    worker_id = uuid.uuid4()
    blocking_print('create worker [{id}]'.format(id=worker_id))

    task_in = CONTEXT.socket(zmq.PULL)
    task_in.connect('tcp://localhost:{port}'.format(port=TASK_PORT))

    result_out = CONTEXT.socket(zmq.REQ)
    result_out.connect('tcp://localhost:{port}'.format(port=RESULT_PORT))

    # sync worker to client
    worker_ack_out = CONTEXT.socket(zmq.REQ)
    worker_ack_out.connect('tcp://localhost:{port}'.format(port=WORKER_ACK_PORT))
    worker_ack_out.send(b'')
    blocking_print('waiting to start worker [{id}]'.format(id=worker_id))
    worker_ack_out.recv()  # blocking wait client to response, then start working process
    blocking_print('worker [{id}] stats'.format(id=worker_id))

    # main working loop
    while True:
        blocking_print('worker [{id}] is waiting for task'.format(id=worker_id))
        task_msg = task_in.recv_json()
        blocking_print('receive task_msg: {msg}'.format(msg=task_msg))
        task = Task(task_msg['id'], task_msg['command'])
        blocking_print('worker [{id}] is working on {task}'.format(id=worker_id, task=task.id))

        action(task)
        task.set_done()

        result_out.send_json(task.__dict__)

        blocking_print('worker [{id}] is sending out result'.format(id=worker_id))
        result_out.recv()


def _sink(tasks):
    sink_id = uuid.uuid4()
    blocking_print('create sink [{id}]'.format(id=sink_id))

    result_in = CONTEXT.socket(zmq.REP)
    result_in.bind('tcp://*:{port}'.format(port=RESULT_PORT))

    while True:
        task_msg = result_in.recv_json()
        task = Task(task_msg['id'], task_msg['command'], task_msg['status'])
        blocking_print('sink [{id}] received result of task {task_id}'.format(id=sink_id, task_id=task.id))
        tasks[task.id] = task
        print(tasks)
        result_in.send(b'')


def simple_action(task):
    blocking_print('procesing task: {id}'.format(id=task.id))
    import random
    time.sleep(random.randint(1, 2))


def start(num_workers=4):
    manager = Manager()
    tasks = manager.dict()
    processes = []

    # create sink
    p = Process(target=_sink, args=(tasks, ))
    processes.append(p)
    p.start()

    # create workers
    for i in range(num_workers):
        p = Process(target=_worker, args=(simple_action,))
        processes.append(p)
        p.start()

    # synchronise active workers
    ack_in = CONTEXT.socket(zmq.REP)
    ack_in.bind('tcp://*:{port}'.format(port=WORKER_ACK_PORT))
    num_active_workers = 0
    while num_active_workers < num_workers:
        ack_in.recv()
        ack_in.send(b'')
        num_active_workers += 1

    # create task_out socket
    task_out = CONTEXT.socket(zmq.PUSH)
    task_out.bind('tcp://*:{port}'.format(port=TASK_PORT))

    return processes, task_out, tasks


def stop(processes):
    for p in processes:
        print('stop process [{pid}]'.format(pid=p.pid))
        p.terminate()


def main():
    processes, task_out, tasks = start()
    for i in range(20):
        task = Task(i, {})
        tasks[task.id] = task
        blocking_print('send task: {task}'.format(task=task.id))
        task_out.send_json(task.__dict__)
        time.sleep(0.5)

    all_task_done = False
    total_check = 0
    while not all_task_done:
        all_task_done = True
        for k, v in tasks.items():
            if not v.is_done():
                all_task_done = False
                break
        blocking_print('Waiting for all tasks done')
        print(tasks)
        time.sleep(1)
        total_check += 1
        if total_check > 50:
            all_task_done = True

    stop(processes)
    print(tasks)

if __name__ == '__main__':
    main()
