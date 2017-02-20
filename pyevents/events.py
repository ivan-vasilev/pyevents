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

    def __iadd__(self, item):
        if not isinstance(item, str) and isinstance(item, Iterable):
            self._list_of_iterables.append(item)
        else:
            if isinstance(self._default_list, list):
                self._default_list.append(item)
            else:
                self._default_list += item

        return self

    def __isub__(self, item):
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

    @property
    def _queue(self):
        if self.__queue is None:
            self.__queue = queue.Queue()

            def call_listeners(q):
                for (task, callback) in iter(q.get, None):
                    logging.getLogger(__name__).debug("Run task from queue: " + str(task))

                    result = task()

                    if result is not None:
                        logging.getLogger(__name__).debug("Task result: " + str(result))

                    if callback is not None:
                        callback(result)

                    q.task_done()

            t = threading.Thread(target=call_listeners, args=(self.__queue,), daemon=True)
            logging.getLogger(__name__).debug("Starting queue thread: " + str(t))
            t.start()

        return self.__queue

    def wrap_async(self, function, callback=None):
        task_queue = self.__queue_by_element(function)

        def wrapper(*args, **kwargs):
            logging.getLogger(__name__).debug(
                "\n===================================================================\nQueue task: " + str(
                    function) + "; Callback: " + str(callback) + "\nQueue task args: " + str(
                    args) + "; kwargs: " + str(
                    kwargs) + "\n===================================================================")

            task_queue.put((functools.partial(function, *args, **kwargs), callback))

        return wrapper

    def __queue_by_element(self, function):
        for l in self._list_of_iterables:
            if isinstance(l, type(self)):
                return l.__queue_by_element(function)

        return self._queue


class _BaseEvent(object):
    """
    Notifies listeners before method execution. For use, check the unit test
    """

    def __init__(self, function):
        super().__init__()
        self._function = function
        self._listeners = AsyncListeners()
        self._listeners_dict = dict()

    def __iadd__(self, listener):
        self._listeners.__iadd__(listener)

        return self

    def __isub__(self, listener):
        self._listeners.__isub__(listener)

        return self

    def __get__(self, obj, objtype):
        result = type(self)(functools.partial(self._function, obj))

        key = hash((obj, self._function))
        if key not in self._listeners_dict:
            self._listeners_dict[key] = AsyncListeners()

        result._listeners = self._listeners_dict[key]

        return result

    def __set__(self, instance, value):
        pass


class before(_BaseEvent):
    """
    Notifies listeners before method execution. For use, check the unit test
    """

    def __call__(self, *args, **kwargs):
        if 'event_callback' in kwargs:
            callback = kwargs['event_callback']
            del kwargs['event_callback']
        else:
            callback = None

        for l in [l for l in self._listeners if l != self]:
            self._listeners.wrap_async(l)(*args, **kwargs)

        self._listeners.wrap_async(self._function, callback=callback)(*args, **kwargs)


class after(_BaseEvent):
    """
    Notifies listeners after method execution. See the unit test on how to use
    """

    def __call__(self, *args, **kwargs):
        if 'event_callback' in kwargs:
            callback = kwargs['event_callback']
            del kwargs['event_callback']
        else:
            callback = None

        def internal_callback(result):
            if callback is not None:
                callback(result)

            for l in [l for l in self._listeners if l != self]:
                self._listeners.wrap_async(l)(result)

        self._listeners.wrap_async(self._function, callback=internal_callback)(*args, **kwargs)
