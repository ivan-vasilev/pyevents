import itertools
import logging
from collections import Iterable
from concurrent.futures import ThreadPoolExecutor


class ChainIterables(object):
    def __init__(self, default_iterable=None):
        self._list_of_iterables = list()
        self._default_iterable = default_iterable if default_iterable is not None else list()
        self.__queue = None

    def __iadd__(self, item):
        if not isinstance(item, str) and isinstance(item, Iterable):
            if item not in self._list_of_iterables:
                self._list_of_iterables.append(item)
        elif isinstance(self._default_iterable, list):
            if item not in self._default_iterable:
                self._default_iterable.append(item)
        else:
            self._default_iterable += item

        return self

    def __isub__(self, item):
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

    def __call__(self, *args, **kwargs):
        for l in [l for l in self if l != self]:
            l(*args, **kwargs)

    def __iadd__(self, item):
        for i in self:
            if i == item:
                return self

        return super().__iadd__(item)


class AsyncListeners(ChainIterables):

    def __init__(self, default_iterable=None):
        super().__init__(default_iterable=default_iterable)
        self.__executor = None

    def __call__(self, *args, **kwargs):
        for l in self:
            self.wrap_async(l, *args, **kwargs)

    def __iadd__(self, item):
        for i in self:
            if i == item:
                return self

        return super().__iadd__(item)

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


class CompositeEvent(list):
    pass
