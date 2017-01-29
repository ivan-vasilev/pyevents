from collections import Iterable
import itertools
import functools


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
        for l in [l for l in self._listeners if l != self]:
            l(*args, **kwargs)

        return self._function(*args, **kwargs)


class after(_BaseEvent):
    """
    Notifies listeners after method execution. See the unit test on how to use
    """

    def __call__(self, *args, **kwargs):
        result = self._function(*args, **kwargs)

        for l in [l for l in self._listeners if l != self]:
            listener_result = l(result)
            result = listener_result if listener_result is not None else result

        return result
