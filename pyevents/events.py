import collections
import functools
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
            if isinstance(item, _EventGenerator):
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
            if isinstance(item, _EventGenerator):
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
        self.__running = False

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

                    try:
                        result = task()
                    except Exception as err:
                        if callback is not None:
                            callback(err)
                        else:
                            logging.getLogger(__name__).exception(err)
                    else:
                        if result is not None:
                            logging.getLogger(__name__).debug("Task result: " + str(result))

                        if callback is not None:
                            callback(result)

                        q.task_done()
                    finally:
                        if not self.__running:
                            return

            t = threading.Thread(target=call_listeners, args=(self.__queue,), daemon=True)
            logging.getLogger(__name__).debug("Starting queue thread: " + str(t))
            self.__running = True
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

            def internal_callback(result):
                if isinstance(result, Exception):
                    raise result
                else:
                    callback(result)

            task_queue.put((functools.partial(function, *args, **kwargs), internal_callback if callback is not None else None))

        return wrapper

    def stop(self):
        self.__running = False

    def __queue_by_element(self, function):
        for l in self._list_of_iterables:
            if isinstance(l, type(self)):
                return l.__queue_by_element(function)

        return self._queue


class GlobalRegister(type):

    global_event_generators = collections.OrderedDict()
    global_listeners = collections.OrderedDict()
    _default_listeners = None

    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)

        if not isinstance(obj, _EventGenerator) and not isinstance(obj, listener):
            for attr in [item[0] for item in type(obj).__dict__.items() if not isinstance(item[1], property)]:
                getattr(obj, attr)

        if isinstance(obj, _EventGenerator):
            if cls.default_listeners is not None:
                obj.listeners = cls.default_listeners

        return obj

    def reset(cls):
        cls.default_listeners = None
        cls.global_event_generators.clear()
        cls.global_listeners.clear()

    @property
    def default_listeners(cls):
        return cls._default_listeners

    @default_listeners.setter
    def default_listeners(cls, default_listeners):
        if cls._default_listeners is not None and isinstance(cls._default_listeners, AsyncListeners):
            cls._default_listeners.stop()

        cls._default_listeners = default_listeners

        for _, e in cls.global_event_generators.items():
            e.listeners = default_listeners if default_listeners is not None else AsyncListeners()

    @property
    def event_generators_list(cls):
        return GlobalRegister.DictToList(cls.global_event_generators)

    @property
    def listeners_list(cls):
        return GlobalRegister.DictToList(cls.global_listeners)

    class DictToList(object):
        def __init__(self, dictionary):
            self._dictionary = dictionary

        def __iter__(self):
            return iter(self._dictionary.values())

        def __isub__(self, item):
            key = None
            for k, v in self._dictionary.items():
                if v == item:
                    key = k
                    break

            del self._dictionary[key]

            return self


class _EventGenerator(object, metaclass=GlobalRegister):
    """
    Base event class that handles listeners
    """

    def __init__(self, function, key=None):
        self._function = function

        self._listeners = None

        if key is None:
            key = hash(function)

        type(self).global_event_generators[key] = self

    @property
    def listeners(self):
        if self._listeners is None:
            self._listeners = AsyncListeners()

        return self._listeners

    @listeners.setter
    def listeners(self, listeners):
        self._listeners = listeners

    def __iadd__(self, listener):
        self.listeners.__iadd__(listener)
        return self

    def __isub__(self, listener):
        self.listeners.__isub__(listener)
        return self

    def __get__(self, obj, objtype=None):
        bound_key = hash((obj, self._function))
        if bound_key not in type(self).global_event_generators:
            type(self)(functools.partial(self._function, obj), bound_key)

        unbound_key = hash(self._function)
        if unbound_key in type(self).global_event_generators:
            del type(self).global_event_generators[unbound_key]

        return type(self).global_event_generators[bound_key]

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
            for l in [l for l in self.listeners if l != self and l != self._function]:
                self.listeners.wrap_async(l)(*args, **kwargs)

            self.listeners.wrap_async(self._function, callback=callback)(*args, **kwargs)
        else:
            for l in [l for l in self.listeners if l != self and l != self._function]:
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
                        for l in [l for l in self.listeners if l != self and l != self._function]:
                            self.listeners.wrap_async(l)(r)
                else:
                    for l in [l for l in self.listeners if l != self and l != self._function]:
                        self.listeners.wrap_async(l)(result)

            self.listeners.wrap_async(self._function, callback=internal_callback)(*args, **kwargs)
        else:
            result = self._function(*args, **kwargs)

            if callback is not None:
                callback(result)

            if isinstance(result, CompositeEvent):
                for r in result:
                    for l in [l for l in self.listeners if l != self and l != self._function]:
                        l(r)
            else:
                for l in [l for l in self.listeners if l != self and l != self._function]:
                    l(result)

            return result


class listener(object, metaclass=GlobalRegister):

    def __init__(self, function, key=None):
        super().__init__()
        self._function = function
        if key is None:
            key = hash(function)

        type(self).global_listeners[key] = self

    def __get__(self, obj, objtype):
        bound_key = hash((obj, self._function))
        if bound_key not in type(self).global_listeners:
            type(self)(functools.partial(self._function, obj), bound_key)

        unbound_key = hash(self._function)
        if unbound_key in type(self).global_listeners:
            del type(self).global_listeners[unbound_key]

        return type(self).global_listeners[bound_key]

    def __call__(self, *args, **kwargs):
        return self._function(*args, **kwargs)


def reset():
    _EventGenerator.reset()


def use_global_event_bus():
    _EventGenerator.default_listeners = AsyncListeners(listener.listeners_list)
