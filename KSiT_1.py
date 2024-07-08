import threading
import queue
import random
import time
import numpy as np
from scipy.stats import rayleigh, norm
import matplotlib.pyplot as plt


def rayleigh_dist(scale):
    return rayleigh.rvs(scale=scale)


def gauss(variance):
    mean = 2
    while True:
        value = norm.ppf(np.random.rand(), mean, np.sqrt(variance))
        if value > 0:
            return value


class WorkerThread(threading.Thread):
    def __init__(self, thread_id, task_queue, result_list):
        super().__init__()
        self.thread_id = thread_id
        self.task_queue = task_queue
        self.result_list = result_list
        self.busy = False

    def run(self):
        while True:
            try:
                task = self.task_queue.get(timeout=1)
            except queue.Empty:
                continue

            if task is None:
                break

            self.busy = True
            task['workerThreadId'] = self.thread_id
            time.sleep(task['time_work'])
            task['timeDoneWorker'] = time.time()
            self.result_list.append(task)
            self.busy = False
            self.task_queue.task_done()


def start_process(scale, variance):
    task_queue = queue.LifoQueue(maxsize=17)
    queue_length_distribution = {}
    result_list = []
    server_prob_list = []
    process_time_limit = 1000
    process_current_time = 0
    task_id = 1
    num_workers = 4

    workers = []
    for i in range(num_workers):
        worker = WorkerThread(i + 1, task_queue, result_list)
        worker.start()
        workers.append(worker)

    while process_current_time <= process_time_limit:

        tau = gauss(variance) / 100
        sig = rayleigh_dist(scale)

        process_current_time += tau * 100

        queue_length = task_queue.qsize()
        if queue_length in queue_length_distribution:
            queue_length_distribution[queue_length] += 1
        else:
            queue_length_distribution[queue_length] = 1

        task = {
            'id': task_id,
            'time_work': sig,
            'time_wait': tau,
            'timeAddedQueue': process_current_time,
            'busy_work': not (len([worker for worker in workers if not worker.busy]) > 0),
            'queue': task_queue.qsize()
        }
        task_id += 1

        if not task_queue.full():
            task_queue.put(task, block=False)
        else:
            task['timeRejected'] = process_current_time
            task['taskRejected'] = True
            result_list.append(task)

            server_prob = {
                'current_time': process_current_time,
                'prob': len(list(filter(lambda item: not item['busy_work'], result_list))) / len(result_list),

            }

            server_prob_list.append(server_prob)

        time.sleep(tau)

    for _ in range(num_workers):
        task_queue.put(None)
    for worker in workers:
        worker.join()

    server_idle_probability = len(list(filter(lambda item: not item['busy_work'], result_list))) / len(result_list)

    print(f"Task count: {len(result_list)}")
    print('--------------------------------------------------------')
    print(f"Tasks: {result_list}")
    print('--------------------------------------------------------')
    print(f"Server idle probability: {server_idle_probability}")
    print('--------------------------------------------------------')
    print(f'{server_prob_list}')
    print('--------------------------------------------------------')
    print(queue_length_distribution)

    total_tasks = sum(queue_length_distribution.values())
    probabilities = {length: count / total_tasks for length, count in queue_length_distribution.items()}

    sorted_lengths = sorted(probabilities.keys())
    sorted_probabilities = [probabilities[length] for length in sorted_lengths]

    plt.figure(figsize=(10, 6))
    plt.plot(sorted_lengths, sorted_probabilities, label = f' sigma= {scale}  variance = {variance}', linewidth=2)
    plt.title('Распределение вероятностей длины очереди L(n)')
    plt.xlabel('Длина очереди (n)')
    plt.ylabel('Вероятность P{длина очереди = n}')
    plt.legend()
    plt.show()

    times = [item['current_time'] for item in server_prob_list]
    probs = [item['prob'] for item in server_prob_list]
    plt.plot(times, probs, linestyle='-', label = f' sigma= {scale}  variance = {variance}',linewidth = 1, color='b')
    plt.xlabel('Время')
    plt.ylabel('Вероятность простоя')
    plt.title('вероятность простоя сервера в произвольный момент времени t')
    plt.legend()
    plt.show()


if __name__ == "__main__":
    start_process(0.5, 1)
    start_process(1, 1)
    start_process(2, 2)

