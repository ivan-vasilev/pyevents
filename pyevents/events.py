import itertools
import logging
import typing
from collections import Iterable
from concurrent.futures import ThreadPoolExecutor


class ChainIterables(object):
    """
    List of event listeners.
    Multiple such lists can be chained.
    """

    def __init__(self, default_iterable=None):
        self._list_of_iterables = list()
        self._default_iterable = default_iterable if default_iterable is not None else list()
        self.__queue = None

    def __iadd__(self, item: typing.Union[typing.Iterable, typing.Callable]):
        """Add listeners or other iterables to the list"""

        if not isinstance(item, str) and isinstance(item, Iterable):
            if item not in self._list_of_iterables:
                self._list_of_iterables.append(item)
        elif isinstance(self._default_iterable, list):
            if item not in self._default_iterable:
                self._default_iterable.append(item)
        else:
            self._default_iterable += item

        return self

    def __isub__(self, item: typing.Union[typing.Iterable, typing.Callable]):
        """Remove listeners or other iterables from the list"""

        if not isinstance(item, str) and isinstance(item, Iterable):
            self._list_of_iterables.remove(item)
        elif isinstance(self._default_iterable, list):
            self._default_iterable.remove(item)
        else:
            self._default_iterable -= item

        return self

    def __iter__(self):
        return iter(itertools.chain(self._default_iterable, *self._list_of_iterables))

    def __len__(self):
        return sum(1 for _ in self.__iter__())


class SyncListeners(ChainIterables):
    """Synchronously call all listeners"""

    def __call__(self, *args, **kwargs):
        for l in self:
            if l != self:
                l(*args, **kwargs)

    def __iadd__(self, item: typing.Union[typing.Iterable, typing.Callable]):
        for i in self:
            if i == item:
                return self

        super().__iadd__(item)

        return self


class AsyncListeners(ChainIterables):
    """Call listeners via ThreadPool"""

    def __init__(self, default_iterable=None):
        super().__init__(default_iterable=default_iterable)
        self.__executor = None

    def __call__(self, *args, **kwargs):
        for l in self:
            self.wrap_async(l, *args, **kwargs)

    def __iadd__(self, item: typing.Union[typing.Iterable, typing.Callable]):
        for i in self:
            if i == item:
                return self

        super().__iadd__(item)

        return self

    @property
    def _executor(self):
        if self.__executor is None:
            self.__executor = ThreadPoolExecutor()

        return self.__executor

    def shutdown(self, wait=True):
        if self.__executor is not None:
            self.__executor.shutdown(wait=wait)

    def wrap_async(self, fn, *args, **kwargs):
        def wrapper():
            logging.getLogger(__name__).debug("Run task from queue: " + str(fn))

            try:
                result = fn(*args, **kwargs)
            except Exception as err:
                logging.getLogger(__name__).exception(err)
                return err
            else:
                if result is not None:
                    logging.getLogger(__name__).debug("Task result: " + str(result.keys() if isinstance(result, dict) else result))

                return result

        executor = self.__executor_by_element(fn)
        return executor.submit(wrapper)

    def __executor_by_element(self, fn):
        for l in self._list_of_iterables:
            if isinstance(l, type(self)):
                return l.__executor_by_element(fn)

        return self._executor


class EventFilter(object):
    """Represents events "view", where only a subset of events will be routed to the given function"""

    def __init__(self, listeners, event_filter: typing.Callable = None, event_transformer: typing.Callable = None):
        """
        :param listeners: listeners
        :param event_filter: function, which returns true/false if the event can be accepted
        :param event_transformer: function that transforms the event. This function should return a *tuple*
        """

        self.listeners = listeners
        self.event_filter = event_filter
        self.event_transformer = event_transformer
        self.functions = dict()

    def __iadd__(self, item: typing.Union[typing.Iterable, typing.Callable]):
        # define a wrapper listener

        fn = None

        if self.event_filter is not None and self.event_transformer is not None:
            def __fn1(*args, **kwargs):
                if self.event_filter(*args, **kwargs):
                    item(*self.event_transformer(*args, **kwargs))

            fn = __fn1
        elif self.event_filter is not None and self.event_transformer is None:
            def __fn2(*args, **kwargs):
                if self.event_filter(*args, **kwargs):
                    item(*args, **kwargs)

            fn = __fn2
        elif self.event_filter is None and self.event_transformer is not None:
            def __fn3(*args, **kwargs):
                item(*self.event_transformer(*args, **kwargs))

            fn = __fn3
        elif self.event_filter is None and self.event_transformer is None:
            def __fn4(*args, **kwargs):
                item(*args, **kwargs)

            fn = __fn4

        self.functions[item] = fn

        self.listeners.__iadd__(fn)

        return self

    def __isub__(self, item: typing.Union[typing.Iterable, typing.Callable]):
        if item in self.functions:
            self.listeners.__isub__(self.functions[item])
            del self.functions[item]
            return self

    def __getattr__(self, name):
        return getattr(self.listeners, name)

    def __call__(self, *args, **kwargs):
        raise Exception("Not Callable")

    def filter(self, event_filter: typing.Callable):
        """
        Represents events "view" over the existing "view". Additional filter on top of the existing one
        :param event_filter: function, which returns true/false if the event can be accepted
        :return: child EventFilter
        """
        return EventFilter(listeners=self, event_filter=event_filter)

    def transform(self, transformer: typing.Callable):
        """
        Represents event transformer over the existing "view". Additional data processing on top of the existing one
        :param transformer: function that transforms the event. This function should return a *tuple*
        :return: child EventFilter
        """
        return EventFilter(listeners=self, event_transformer=transformer)

    def filter_and_transform(self, event_filter: typing.Callable = None, event_transformer: typing.Callable = None):
        """
        Represents events "view" over the existing "view". Additional filter and/or data processing on top of the existing one
        :param event_filter: function, which returns true/false if the event can be accepted
        :param event_transformer: function that transforms the event. This function should return a *tuple*
        :return: child EventFilter
        """
        return EventFilter(listeners=self, event_filter=event_filter, event_transformer=event_transformer)


class CompositeEvent(list):
    pass
