import functools
import itertools
import queue
import threading
from collections import Iterable
import logging


class LinkedLists(object):
    def __init__(self):
        self._list_of_iterables = list()
        self._default_list = list()
        self.__queue = None

    def __iadd__(self, item):
        if not isinstance(item, str) and isinstance(item, Iterable):
            self._list_of_iterables.append(item)
        else:
            if __name__ == item.__module__ and hasattr(item, '_function'):
                item = getattr(item, '_function')

            if isinstance(self._default_list, list):
                self._default_list.append(item)
            else:
                self._default_list += item

        return self

    def __isub__(self, item):
        if not isinstance(item, str) and isinstance(item, Iterable):
            self._list_of_iterables.remove(item)
        else:
            if __name__ == item.__module__ and hasattr(item, '_function'):
                item = getattr(item, '_function')

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


class AsyncListeners(LinkedLists):
    def __init__(self):
        super().__init__()
        self.__queue = None

    def __call__(self, *args, **kwargs):
        for l in self:
            self.wrap_async(l)(*args, **kwargs)

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


class CompositeEvent(list):
    pass


class before(_BaseEvent):
    """
    Notifies listeners before method execution. For use, check the unit test
    """

    def __call__(self, *args, run_async=True, callback=None, **kwargs):
        if run_async:
            for l in [l for l in self._listeners if l != self and l != self._function]:
                self._listeners.wrap_async(l)(*args, **kwargs)

            self._listeners.wrap_async(self._function, callback=callback)(*args, **kwargs)
        else:
            for l in [l for l in self._listeners if l != self and l != self._function]:
                l(*args, **kwargs)

            result = self._function(*args, **kwargs)

            if callback is not None:
                callback(result)

            return result


class after(_BaseEvent):
    """
    Notifies listeners after method execution. See the unit test on how to use
    """

    def __call__(self, *args, run_async=True, callback=None, **kwargs):
        if run_async:
            def internal_callback(result):
                if callback is not None:
                    callback(result)

                if isinstance(result, CompositeEvent):
                    for r in result:
                        for l in [l for l in self._listeners if l != self and l != self._function]:
                            self._listeners.wrap_async(l)(r)
                else:
                    for l in [l for l in self._listeners if l != self and l != self._function]:
                        self._listeners.wrap_async(l)(result)

            self._listeners.wrap_async(self._function, callback=internal_callback)(*args, **kwargs)
        else:
            result = self._function(*args, **kwargs)

            if callback is not None:
                callback(result)

            if isinstance(result, CompositeEvent):
                for r in result:
                    for l in [l for l in self._listeners if l != self and l != self._function]:
                        l(r)
            else:
                for l in [l for l in self._listeners if l != self and l != self._function]:
                    l(result)

            return result
