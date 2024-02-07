import psutil
import multiprocessing as mp
import multiprocessing.queues as mpq
import functools
import dill
from typing import Tuple, Callable, Dict, Optional, Iterable
from time import time
import datetime
import logging

__all__ = ["killer_pmap"]


"""
Part of the following code was taken from:
https://flipdazed.github.io/blog/quant%20dev/parallel-functions-with-timeouts
"""


def kill_child_processes(parent_pid):
    try:
        parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        return
    children = parent.children(recursive=True)
    for process in children:
        try:
            logging.debug(f"Timeout! Trying to terminate child {process.pid}")
            process.terminate()
        except psutil.NoSuchProcess:
            pass
    gone, alive = psutil.wait_procs(children, timeout=5)
    for process in alive:
        try:
            logging.debug(f"Timeout! Killing child {process.pid}")
            process.kill()
        except psutil.NoSuchProcess:
            pass


class AnalysisTimeoutError(Exception):

    def __init__(self, func, timeout):
        self.t = timeout
        self.f_name = func.__name__

    def __str__(self):
        return f"function '{self.f_name}' timed out after {self.t}s"


def lemmiwinks(func: Callable, args: Tuple[object], kwargs: Dict[str, object],
               q: mp.Queue):
    """lemmiwinks crawls into the unknown"""
    q.put(dill.loads(func)(*args, **kwargs))


def killer_call(func: Callable = None, timeout: int = 10) -> Callable:
    """
    Single function call with a timeout

    Args:
        func: the function
        timeout: The timeout in seconds
    """

    if not isinstance(timeout, int):
        raise ValueError(f"timeout needs to be an int. Got: {timeout}")

    if func is None:
        return functools.partial(killer_call, timeout=timeout)

    @functools.wraps(killer_call)
    def _inners(*args, **kwargs) -> object:
        q_worker = mp.Queue()
        proc = mp.Process(target=lemmiwinks, args=(dill.dumps(func), args,
                                                   kwargs, q_worker))
        proc.start()
        try:
            return q_worker.get(timeout=timeout)
        except mpq.Empty:
            raise AnalysisTimeoutError(func, timeout)
        finally:
            try:
                proc.terminate()
            except:
                pass
    return _inners


def queue_mgr(func_str: str, q_in: mp.Queue, q_out: mp.Queue, timeout: int,
              pid: int) -> object:
    """
    Controls the main workflow of cancelling the function calls that take too long
    in the parallel map

    Args:
        func_str: The function, converted into a string via dill (more stable than pickle)
        q_in: The input queue
        q_out: The output queue
        timeout: The timeout in seconds
        pid: process id
    """
    total_elements = q_in.qsize()
    start_time = time()
    done = 0
    start_proc_time = 0

    while True:
        #timeout is needed because the queue may get stuck for some seconds
        #possibly from loading the next elements
        try:
            positioning, x = q_in.get(True, timeout=10)
        except mpq.Empty:
            break

        q_worker = mp.Queue()
        proc = mp.Process(target=lemmiwinks, args=(func_str, (x,), {},
                                                   q_worker,))
        proc.start()
        try:
            start_proc_time = time()
            if type(x) == str:
                logging.debug(f"[{pid}]: Processing {positioning}: {x}")
            res = q_worker.get(timeout=timeout)
            q_out.put((positioning, res))
        except mpq.Empty:
            q_out.put((positioning, None))
            with open("apks_not_processed.txt", "a") as f:
                f.write(f"{x}\n")
            logging.debug(f"[{pid}]: {positioning}: timed out ({timeout}s)")
        finally:
            try:
                kill_child_processes(proc.pid)
                proc.terminate()
                done += 1
                perc = int((positioning / total_elements) * 100)
                est_time = (total_elements - positioning) * \
                           ((time() - start_time) / positioning)
                est_time = str(datetime.timedelta(seconds=est_time))

                logging.debug(
                    f"[{pid}]: {positioning}: terminated in "
                    f"{datetime.timedelta(seconds=time() - start_proc_time)} "
                    f"secs")
                logging.debug(
                    f"[{pid}]: {perc}% done, {positioning}/{total_elements},"
                    f" {est_time} secs remaining")
                proc.close()
            except:
                pass
    logging.debug(f"[{pid}]: completed in "
                  f"{datetime.timedelta(seconds=time() - start_time)} secs!")


def killer_pmap(func: Callable, iterable: Iterable, cpus: Optional[int] = None,
                timeout: int = 4):
    """
    Parallelization of func across the iterable with a timeout at each evaluation

    Args:
        func: The function
        iterable: The iterable to map func over
        cpus: The number of cpus to use. Default is the use max - 2.
        timeout: kills the func calls if they take longer than this in seconds
    """

    if cpus is None:
        cpus = max(mp.cpu_count() - 2, 1)
        if cpus == 1:
            raise ValueError("Not enough CPUs to parallelize. "
                             "You only have 1 CPU!")
        else:
            logging.debug(f"Optimising for {cpus} processors")

    q_in = mp.Queue()
    q_out = mp.Queue()
    sent = [q_in.put((i, x)) for i, x in enumerate(iterable)]

    processes = [mp.Process(
        target=queue_mgr, args=(dill.dumps(func), q_in, q_out, timeout, pid))
        for pid in range(cpus)]
    logging.debug(f"Started {len(processes)} processes")
    for proc in processes:
        proc.start()

    result = [q_out.get() for _ in sent]

    logging.debug("Ending processes...")
    for proc in processes:
        logging.debug(proc.pid)
        kill_child_processes(proc.pid)
        proc.terminate()

    logging.debug("Returning data")
    return [x for _, x, in sorted(result)]
