import functools
import itertools
import queue
import threading
from collections import Iterable
import asyncio


class ChainedLists(object):
    def __init__(self):
        self.list_of_iterables = list()
        self.default_list = list()

    def __iadd__(self, item):
        if not isinstance(item, str) and isinstance(item, Iterable):
            self.list_of_iterables.append(item)
        else:
            if isinstance(self.default_list, list):
                self.default_list.append(item)
            else:
                self.default_list += item

        return self

    def __isub__(self, item):
        if not isinstance(item, str) and isinstance(item, Iterable):
            self.list_of_iterables.remove(item)
        else:
            if isinstance(self.default_list, list):
                self.default_list.remove(item)
            else:
                self.default_list -= item

        return self

    def __iter__(self):
        self.chain = itertools.chain(self.default_list, *self.list_of_iterables)
        return self

    def __next__(self):
        return next(self.chain)


class _AsyncListeners(threading.Thread):
    def __init__(self):
        super().__init__()

        self.jobs_queue = queue.Queue()
        self.results_queue = queue.Queue()

    def run(self):
        for (f, args, kwargs) in iter(self.jobs_queue, None):
            result = f(*args, **kwargs)
            self.results_queue.put((f, result))


class _BaseEvent(object):
    """
    Notifies listeners before method execution. For use, check the unit test
    """

    def __init__(self, function):
        super().__init__()
        self._function = function
        self._listeners = ChainedLists()
        self._listeners_dict = dict()

    def __iadd__(self, listener):
        self._listeners.__iadd__(listener)
        return self

    def __isub__(self, listener):
        self._listeners.__isub__(listener)
        return self

    def __get__(self, obj, objtype):
        if obj not in self._listeners_dict:
            self._listeners_dict[obj] = ChainedLists()

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
        if threading.current_thread() != threading.main_thread():
            try:
                asyncio.get_event_loop()
            except RuntimeError:
                asyncio.set_event_loop(asyncio.new_event_loop())

        tasks = [asyncio.coroutine(functools.partial(l, *args, **kwargs))() for l in self._listeners if l != self]
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks))

        if asyncio.iscoroutinefunction(self._function):
            result = asyncio.get_event_loop().run_until_complete(asyncio.coroutine(functools.partial(self._function, *args, **kwargs))())
        else:
            result = self._function(*args, **kwargs)

        return result

import threading


class after(_BaseEvent):
    """
    Notifies listeners after method execution. See the unit test on how to use
    """

    def __call__(self, *args, **kwargs):
        if threading.current_thread() != threading.main_thread():
            try:
                asyncio.get_event_loop()
            except RuntimeError:
                asyncio.set_event_loop(asyncio.new_event_loop())

        if asyncio.iscoroutinefunction(self._function):
            result = asyncio.get_event_loop().run_until_complete(asyncio.coroutine(functools.partial(self._function, *args, **kwargs))())
        else:
            result = self._function(*args, **kwargs)

        tasks = [asyncio.coroutine(functools.partial(l, result))() for l in self._listeners if l != self]
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks))

        return result
