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
            t.start()

            logging.getLogger(__name__).debug("Queue thread started: " + str(t))

        return self.__queue

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

    def add_to_queue(self, function, callback=None):
        task_queue = self.__queue_by_element(function)

        def wrapper(*args, **kwargs):
            if callback is not None:
                logging.getLogger(__name__).debug("Queue task: " + str(function) + "; Callback: " + str(callback))
            else:
                logging.getLogger(__name__).debug("Queue task: " + str(function))

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

    def __init__(self, function):
        """
        to obtain the result of a function, you can set the callback parameter to a function with one parameter
        :param function:
        """
        super().__init__(function)

        self.callback = None

    def __call__(self, *args, **kwargs):
        for l in [l for l in self._listeners if l != self]:
            self._listeners.add_to_queue(l)(*args, **kwargs)

        self._listeners.add_to_queue(self._function, self.callback)(*args, **kwargs)


class after(_BaseEvent):
    """
    Notifies listeners after method execution. See the unit test on how to use
    """
    def __init__(self, function):
        """
        to obtain the result of a function, you can set the callback parameter to a function with one parameter
        :param function:
        """
        super().__init__(function)

        self.callback = None

    def __call__(self, *args, **kwargs):
        def callback(result):
            if self.callback is not None:
                self.callback(result)

            for l in [l for l in self._listeners if l != self]:
                self._listeners.add_to_queue(l)(result)

        self._listeners.add_to_queue(self._function, callback=callback)(*args, **kwargs)
