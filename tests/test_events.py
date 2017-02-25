import unittest
from pyevents.events import *


class TestEvents(unittest.TestCase):
    """
    Test events
    """

    def test_before_1(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_before': False}

        @before
        def method_with_before(x):
            self.assertTrue(listeners_called['listener_1'])
            self.assertTrue(listeners_called['listener_2'])
            listeners_called['method_with_before'] = x

        def listener_1(x):
            listeners_called['listener_1'] = x

        def listener_2(x):
            listeners_called['listener_2'] = x

        e = threading.Event()

        method_with_before += listener_1
        method_with_before += listener_2
        method_with_before(True, callback=lambda result: e.set())

        e.wait()

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertTrue(listeners_called['method_with_before'])

    def test_before_1_sync(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_before': False}

        @before
        def method_with_before(x):
            self.assertTrue(listeners_called['listener_1'])
            self.assertTrue(listeners_called['listener_2'])
            listeners_called['method_with_before'] = x

        def listener_1(x):
            listeners_called['listener_1'] = x

        def listener_2(x):
            listeners_called['listener_2'] = x

        method_with_before += listener_1
        method_with_before += listener_2
        method_with_before(True, run_async=False)

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertTrue(listeners_called['method_with_before'])

    def test_before_2(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_before': False}

        e = threading.Event()

        class TestClass(object):
            @before
            def method_with_before(self):
                listeners_called['method_with_before'] = True
                e.set()

        def listener_1(*args, **kwargs):
            listeners_called['listener_1'] = True

        def listener_2(*args, **kwargs):
            listeners_called['listener_2'] = True

        listeners = [listener_1, listener_2]

        test_class = TestClass()
        test_class.method_with_before += listeners
        test_class.method_with_before()

        e.wait()

        self.assertEqual(len(listeners), 2)
        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertTrue(listeners_called['method_with_before'])

    def test_before_3(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_before': False}

        e = threading.Event()

        def method_with_before(x):
            self.assertTrue(listeners_called['listener_1'])
            self.assertTrue(listeners_called['listener_2'])
            listeners_called['method_with_before'] = x
            e.set()

        before_wrapper = before(method_with_before)

        def listener_1(x):
            listeners_called['listener_1'] = x

        def listener_2(x):
            listeners_called['listener_2'] = x

        before_wrapper += listener_1
        before_wrapper += listener_2
        before_wrapper(True)

        e.wait()

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertTrue(listeners_called['method_with_before'])

    def test_after_1(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_after': False}

        @after
        def method_with_after():
            self.assertFalse(listeners_called['listener_1'])
            self.assertFalse(listeners_called['listener_2'])
            listeners_called['method_with_after'] = True

        e1 = threading.Event()

        def listener_1(*args):
            listeners_called['listener_1'] = True
            e1.set()

        e2 = threading.Event()

        def listener_2(*args):
            listeners_called['listener_2'] = True
            e2.set()

        e = threading.Event()

        method_with_after += listener_1
        method_with_after += listener_2
        method_with_after(callback=lambda result: e.set())

        e.wait()
        self.assertTrue(listeners_called['method_with_after'])

        e1.wait()
        e2.wait()

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])

    def test_after_1_sync(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_after': False}

        @after
        def method_with_after():
            self.assertFalse(listeners_called['listener_1'])
            self.assertFalse(listeners_called['listener_2'])
            listeners_called['method_with_after'] = True

        e1 = threading.Event()

        def listener_1(*args):
            listeners_called['listener_1'] = True

        e2 = threading.Event()

        def listener_2(*args):
            listeners_called['listener_2'] = True

        method_with_after += listener_1
        method_with_after += listener_2
        method_with_after(run_async=False)

        self.assertTrue(listeners_called['method_with_after'])

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])

    def test_after_2(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_after': False}

        @after
        def method_with_after():
            listeners_called['method_with_after'] = True

        e1 = threading.Event()

        def listener_1(*args):
            listeners_called['listener_1'] = True
            e1.set()

        e2 = threading.Event()

        def listener_2(*args):
            listeners_called['listener_2'] = True
            e2.set()

        listeners = [listener_1, listener_2]
        method_with_after += listeners
        method_with_after()

        e1.wait()
        e2.wait()

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertTrue(listeners_called['method_with_after'])

    def test_source_combination(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_before': False}

        listeners = list()

        e = threading.Event()

        @before
        def method_with_before():
            self.assertTrue(listeners_called['listener_1'])
            self.assertTrue(listeners_called['listener_2'])
            listeners_called['method_with_before'] = True
            e.set()

        def listener_1():
            self.assertFalse(listeners_called['listener_1'])
            listeners_called['listener_1'] = True

        def listener_2():
            self.assertFalse(listeners_called['listener_2'])
            listeners_called['listener_2'] = True

        listeners.append(listener_1)
        method_with_before += listeners
        method_with_before += listener_2
        method_with_before()

        e.wait()

        self.assertEqual(len(listeners), 1)
        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertTrue(listeners_called['method_with_before'])

    def test_multiple_lists(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_before': False}

        e = threading.Event()

        @before
        def method_with_before():
            self.assertTrue(listeners_called['listener_1'])
            self.assertTrue(listeners_called['listener_2'])
            listeners_called['method_with_before'] = True
            e.set()

        def listener_1():
            listeners_called['listener_1'] = True

        def listener_2():
            listeners_called['listener_2'] = True

        method_with_before += listener_1
        method_with_before += [listener_2]
        method_with_before()

        e.wait()

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertTrue(listeners_called['method_with_before'])

    def test_remove_listeners(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'listener_3': False, 'listener_4': False, 'method_with_before': False}

        e = threading.Event()

        @before
        def method_with_before():
            self.assertFalse(listeners_called['listener_1'])
            self.assertTrue(listeners_called['listener_2'])
            self.assertFalse(listeners_called['listener_3'])
            self.assertTrue(listeners_called['listener_4'])
            listeners_called['method_with_before'] = True
            e.set()

        def listener_1():
            listeners_called['listener_1'] = True

        def listener_2():
            listeners_called['listener_2'] = True

        def listener_3():
            listeners_called['listener_2'] = True

        def listener_4():
            listeners_called['listener_4'] = True

        method_with_before += listener_1
        method_with_before += listener_2

        listener_3_list = [listener_3]
        method_with_before += listener_3_list
        method_with_before += [listener_4]

        method_with_before -= listener_1
        method_with_before -= listener_3_list

        method_with_before()

        e.wait()

        self.assertFalse(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertFalse(listeners_called['listener_3'])
        self.assertTrue(listeners_called['listener_4'])
        self.assertTrue(listeners_called['method_with_before'])

    def test_multiple_classes(self):
        class Subject(object):
            def __init__(self):
                self.counter = 0
                self.e = threading.Event()

            @before
            def on_stuff(self):
                self.e.set()

        # Now define an event handler, the observer
        handler_1_calls = list()

        def handler1(*args, **kwargs):
            handler_1_calls.append(1)

        handler_2_calls = list()

        def handler2(*args, **kwargs):
            handler_2_calls.append(1)

        sub = Subject()
        sub.on_stuff += handler1

        sub2 = Subject()
        sub2.on_stuff += handler2

        sub.on_stuff()
        sub2.on_stuff()

        sub.e.wait()
        sub2.e.wait()

        self.assertEqual(len(handler_1_calls), 1)
        self.assertEqual(len(handler_2_calls), 1)

    def test_listeners(self):
        listeners = AsyncListeners()

        listeners_called = {'listener_1': False, 'listener_2': False}

        e1 = threading.Event()

        def listener_1(x):
            listeners_called['listener_1'] = x
            e1.set()

        e2 = threading.Event()

        def listener_2(x):
            listeners_called['listener_2'] = x
            e2.set()

        listeners += listener_1
        listeners += listener_2

        listeners(True)

        e1.wait()
        e2.wait()

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])

    def test_same_method(self):
        listeners = AsyncListeners()

        entries = {'function': False, 'function_to_function_1': False, 'function_1_to_function_2': False, 'function_2_to_function_1': False}

        @after
        def function():
            entries['function'] = True
            return 'function_to_function_1'

        function += listeners

        @after
        def function_1(param):
            if param == 'function_to_function_1':
                entries[param] = True
                return 'function_1_to_function_2'

        function_1 += listeners
        listeners += function_1

        e = threading.Event()

        @after
        def function_2(param):
            if param == 'function_1_to_function_2':
                entries[param] = True
                e.set()

        function_2 += listeners
        listeners += function_2

        function()

        e.wait()

        for k, v in entries.values():
            self.assertTrue(v)

if __name__ == '__main__':
    unittest.main()
