import collections
import functools
import gc
import itertools
import logging
import queue
import threading
from collections import Iterable


class ChainIterables(object):
    def __init__(self, default_iterable=None):
        self._list_of_iterables = list()
        self._default_iterable = default_iterable if default_iterable is not None else list()
        self.__queue = None

    def __iadd__(self, item):
        if not isinstance(item, str) and isinstance(item, Iterable):
            if item not in self._list_of_iterables:
                self._list_of_iterables.append(item)
        else:
            if __name__ == item.__module__ and hasattr(item, '_function'):
                item = getattr(item, '_function')

            if isinstance(self._default_iterable, list):
                if item not in self._default_iterable:
                    self._default_iterable.append(item)
            else:
                self._default_iterable += item

        return self

    def __isub__(self, item):
        if not isinstance(item, str) and isinstance(item, Iterable):
            self._list_of_iterables.remove(item)
        else:
            if __name__ == item.__module__ and hasattr(item, '_function'):
                item = getattr(item, '_function')

            if isinstance(self._default_iterable, list):
                self._default_iterable.remove(item)
            else:
                self._default_iterable -= item

        return self

    def __iter__(self):
        return iter(itertools.chain(self._default_iterable, *self._list_of_iterables))


class AsyncListeners(ChainIterables):
    def __init__(self, default_iterable=None):
        super().__init__(default_iterable=default_iterable)
        self.__queue = None

    def __call__(self, *args, **kwargs):
        for l in self:
            self.wrap_async(l)(*args, **kwargs)

    def __iadd__(self, item):
        for i in self:
            if i == item:
                return self

        super().__iadd__(item)

        return self

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


class _GlobalRegister(type):

    event_generators = collections.OrderedDict()
    listeners = collections.OrderedDict()
    _default_listeners = None

    @property
    def default_listeners(cls):
        return cls._default_listeners

    @default_listeners.setter
    def default_listeners(cls, default_listeners):
        if cls._default_listeners is not None:
            for _, e in cls.event_generators.items():
                e -= cls._default_listeners

        cls._default_listeners = default_listeners

        for _, e in cls.event_generators.items():
            e += cls._default_listeners

    @property
    def event_generators_list(cls):
        return _GlobalRegister.DictToList(cls.event_generators)

    @property
    def listeners_list(cls):
        return _GlobalRegister.DictToList(cls.listeners)

    class DictToList(object):
        def __init__(self, dictionary):
            self.dictionary = dictionary

        def __iter__(self):
            return iter(self.dictionary.values())


class _EventGenerator(object, metaclass=_GlobalRegister):
    """
    Base event class that handles listeners
    """

    def __init__(self, function, key=None):
        self._function = function
        self._listeners = AsyncListeners()

        if hasattr(function, 'func'):
            print (function)

        if type(self).default_listeners is not None:
            self._listeners += type(self).default_listeners

        if key is None:
            key = hash(function)

        type(self).event_generators[key] = self

    def __iadd__(self, listener):
        self._listeners.__iadd__(listener)
        return self

    def __isub__(self, listener):
        self._listeners.__isub__(listener)
        return self

    def __get__(self, obj, objtype=None):
        bound_key = hash((obj, self._function))
        if bound_key not in type(self).event_generators:
            type(self)(functools.partial(self._function, obj), bound_key)

        unbound_key = hash(self._function)
        if unbound_key in type(self).event_generators:
            del type(self).event_generators[unbound_key]

        return type(self).event_generators[bound_key]

    def __set__(self, instance, value):
        pass


class CompositeEvent(list):
    pass


class before(_EventGenerator):
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


class after(_EventGenerator):
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


class listener(object, metaclass=_GlobalRegister):

    def __init__(self, function, key=None):
        super().__init__()
        self._function = function
        if key is None:
            key = hash(function)

        type(self).listeners[key] = self

    def __get__(self, obj, objtype):
        bound_key = hash((obj, self._function))
        if bound_key not in type(self).listeners:
            type(self)(functools.partial(self._function, obj), bound_key)

        unbound_key = hash(self._function)
        if unbound_key in type(self).listeners:
            del type(self).listeners[unbound_key]

        return type(self).listeners[bound_key]

    def __call__(self, *args, **kwargs):
        return self._function(*args, **kwargs)


def link_all():
    def __qualapth(obj):
        split = obj.__qualname__.split('.')
        return '.'.join(obj.__qualname__.split('.')[:-1]) if len(split) > 1 else obj

    class_event_generators = dict()
    class_listeners = dict()

    for obj in gc.get_objects():
        try:
            cond = isinstance(obj, _EventGenerator) and not isinstance(obj._function, functools.partial)
        except:
            pass

        if cond:
            qualpath = __qualapth(obj._function)
            if qualpath not in class_event_generators:
                class_event_generators[qualpath] = list()

            class_event_generators[qualpath].append(obj._function)
        else:
            try:
                cond = isinstance(obj, listener) and not isinstance(obj._function, functools.partial)
            except:
                pass

            if cond:
                qualpath = __qualapth(obj._function)
                if qualpath not in class_listeners:
                    class_listeners[qualpath] = list()

                class_listeners[qualpath].append(obj._function)
    for obj in gc.get_objects():
        if type(obj).__qualname__ in class_event_generators:
            for attr in class_event_generators[type(obj).__qualname__]:
                getattr(obj, attr.__name__)

        if type(obj).__qualname__ in class_listeners:
            for attr in class_listeners[type(obj).__qualname__]:
                getattr(obj, attr.__name__)

    _EventGenerator.default_listeners = AsyncListeners(listener.listeners_list)
