from abc import *
from collections import Iterable
import itertools


class _BaseDecorator(metaclass=ABCMeta):
    """
    Base innder decorator. Necessary for iadd/isub methods to work and to have parameters simultaneously
    """

    def __init__(self):
        self.list_of_listener_iterables = list()
        self.default_listeners = list()

    def __iadd__(self, listener):
        if not isinstance(listener, str) and isinstance(listener, Iterable):
            self.list_of_listener_iterables.append(listener)
        else:
            if isinstance(self.default_listeners, list):
                self.default_listeners.append(listener)
            else:
                self.default_listeners += listener

        return self

    def __isub__(self, listener):
        if not isinstance(listener, str) and isinstance(listener, Iterable):
            self.list_of_listener_iterables.remove(listener)
        else:
            if isinstance(self.default_listeners, list):
                self.default_listeners.remove(listener)
            else:
                self.default_listeners -= listener

        return self

    def _call_listeners(self, *args, **kwargs):
        for f in itertools.chain(self.default_listeners, *self.list_of_listener_iterables):
            f(*args, **kwargs)

FUNCTION_OUTPUT = "function_output"


class before(_BaseDecorator):
    """
    Notifies listeners before method execution. For use, check the unit test
    """

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def __call__(self, *args, **kwargs):
        self._call_listeners(*args, **kwargs)
        return self.fn(*args, **kwargs)


class after(_BaseDecorator):
    """
    Notifies listeners after method execution. See the unit test on how to use
    """

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def __call__(self, *args, **kwargs):
        result = self.fn(*args, **kwargs)
        if result is not None:
            kwargs[FUNCTION_OUTPUT] = result

        self._call_listeners(*args, **kwargs)

        return result
