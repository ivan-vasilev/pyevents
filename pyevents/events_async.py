import functools
import itertools
import queue
import threading
from collections import Iterable
import logging


class AsyncListeners(object):

    def __init__(self):
        self._list_of_iterables = list()
        self._default_list = list()
        self.__queue = None
        self._lock = threading.RLock()

    @property
    def _queue(self):
        if self.__queue is None:
            self.__queue = queue.Queue()

            def call_listeners(q):
                for (task, callback) in iter(q.get, None):
                    logging.getLogger(__name__).debug("Run task from queue: " + str(task))

                    result = task()

                    logging.getLogger(__name__).debug("Task result: " + str(result))

                    if callback is not None:
                        callback(result)

                    q.task_done()

            t = threading.Thread(target=call_listeners, args=(self.__queue,), daemon=True)
            t.start()

            logging.getLogger(__name__).debug("Queue thread started: " + str(t))

        return self.__queue

    def __iadd__(self, item):
        with self._lock:
            if not isinstance(item, str) and isinstance(item, Iterable):
                self._list_of_iterables.append(item)
            else:
                if isinstance(self._default_list, list):
                    self._default_list.append(item)
                else:
                    self._default_list += item

        return self

    def __isub__(self, item):
        with self._lock:
            if not isinstance(item, str) and isinstance(item, Iterable):
                self._list_of_iterables.remove(item)
            else:
                if isinstance(self._default_list, list):
                    self._default_list.remove(item)
                else:
                    self._default_list -= item

        return self

    def __iter__(self):
        self.chain = itertools.chain(self._default_list, *self._list_of_iterables)
        return self

    def __next__(self):
        return next(self.chain)

    def add_to_queue(self, function, callback, wait_for_result=False):
        return AsyncListeners.CallWrapper(function, self.__queue_by_element(function), wait_for_result)

    def __queue_by_element(self, function):
        for l in self._list_of_iterables:
            if isinstance(l, type(self)):
                return l.__queue_by_element(function)

        return self._queue

    class CallWrapper(object):
        def __init__(self, function, task_queue, callback, wait_for_result=True):
            if isinstance(function, type(self)):
                raise ValueError("Cannot schedule recursive functions")

            self._function = function
            self._task_queue = task_queue
            self._wait_for_result = wait_for_result
            self._lock = threading.Lock()
            self._callback = callback

        def __call__(self, *args, **kwargs):
            with self._lock:
                if self._wait_for_result:
                    e = threading.Event()

                    def callback(result):
                        e.result = result
                        e.set()

                    logging.getLogger(__name__).debug(
                        "Queue task (wait for result): " + str(self._function))

                    self._task_queue.put((functools.partial(self._function, *args, **kwargs), callback))

                    logging.getLogger(__name__).debug("Queue size: " + str(self._task_queue.qsize()) + "; Unfinished tasks: " + str(self._task_queue.unfinished_tasks))

                    e.wait()

                    logging.getLogger(__name__).debug("Result: " + str(e.result) + " Task: " + str(self._function))

                    return e.result
                else:
                    logging.getLogger(__name__).debug(
                        "Queue task (don't wait for result): " + str(self._function))
                    self._task_queue.put((functools.partial(self._function, *args, **kwargs), self._callback))
                    logging.getLogger(__name__).debug("Task finished: " + str(self._function))


class _BaseEvent(object):
    """
    Notifies listeners before method execution. For use, check the unit test
    """

    def __init__(self, function):
        super().__init__()
        self._function = function
        self._listeners = AsyncListeners()
        self._listeners_dict = dict()
        self._lock = threading.RLock()

    def __iadd__(self, listener):
        self._listeners.__iadd__(listener)

        return self

    def __isub__(self, listener):
        self._listeners.__isub__(listener)

        return self

    def __get__(self, obj, objtype):
        with self._lock:
            if obj not in self._listeners_dict:
                self._listeners_dict[obj] = AsyncListeners()

            result = type(self)(functools.partial(self._function, obj))
            result._listeners = self._listeners_dict[obj]

            return result

    def __set__(self, instance, value):
        pass


class before(_BaseEvent):
    """
    Notifies listeners before method execution. For use, check the unit test
    """

    def __call__(self, *args, **kwargs):
        for l in [l for l in self._listeners if l != self]:
            self._listeners.add_to_queue(l, wait_for_result=False)(*args, **kwargs)

        return self._listeners.add_to_queue(self._function, wait_for_result=True)(*args, **kwargs)


class after(_BaseEvent):
    """
    Notifies listeners after method execution. See the unit test on how to use
    """

    def __call__(self, *args, **kwargs):
        result = self._listeners.add_to_queue(self._function, wait_for_result=True)(*args, **kwargs)

        for l in [l for l in self._listeners if l != self]:
            self._listeners.add_to_queue(l, wait_for_result=False)(result)

        return result
