import unittest
import pyevents.events as events
import threading


class TestEvents(unittest.TestCase):
    """
    Test events
    """

    def setUp(self):
        events.reset()

    def test_before_1(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_before': False}

        @events.before
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
        method_with_before(True)

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertTrue(listeners_called['method_with_before'])

    def test_before_1_sync(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_before': False}

        @events.before
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

        class TestClass(object):
            @events.before
            def method_with_before(self):
                listeners_called['method_with_before'] = True

        def listener_1(*args, **kwargs):
            listeners_called['listener_1'] = True

        def listener_2(*args, **kwargs):
            listeners_called['listener_2'] = True

        listeners = [listener_1, listener_2]

        test_class = TestClass()
        test_class.method_with_before += listeners
        test_class.method_with_before()

        self.assertEqual(len(listeners), 2)
        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertTrue(listeners_called['method_with_before'])

    def test_before_3(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_before': False}

        def method_with_before(x):
            self.assertTrue(listeners_called['listener_1'])
            self.assertTrue(listeners_called['listener_2'])
            listeners_called['method_with_before'] = x

        before_wrapper = events.before(method_with_before)

        def listener_1(x):
            listeners_called['listener_1'] = x

        def listener_2(x):
            listeners_called['listener_2'] = x

        before_wrapper += listener_1
        before_wrapper += listener_2
        before_wrapper(True)

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertTrue(listeners_called['method_with_before'])

    def test_before_4(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_before': False}

        class TestClass(object):

            @staticmethod
            @events.before
            def method_with_before():
                listeners_called['method_with_before'] = True

        def listener_1(*args, **kwargs):
            listeners_called['listener_1'] = True

        def listener_2(*args, **kwargs):
            listeners_called['listener_2'] = True

        listeners = [listener_1, listener_2]

        test_class = TestClass()
        test_class.method_with_before += listeners
        test_class.method_with_before()

        self.assertEqual(len(listeners), 2)
        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertTrue(listeners_called['method_with_before'])

    def test_after_1(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_after': False}

        @events.after
        def method_with_after():
            self.assertFalse(listeners_called['listener_1'])
            self.assertFalse(listeners_called['listener_2'])
            listeners_called['method_with_after'] = True
            return True

        e1 = threading.Event()

        def listener_1(result):
            listeners_called['listener_1'] = result
            e1.set()

        e2 = threading.Event()

        def listener_2(result):
            listeners_called['listener_2'] = result
            e2.set()

        method_with_after += listener_1
        method_with_after += listener_2
        method_with_after()

        self.assertTrue(listeners_called['method_with_after'])

        e1.wait()
        e2.wait()

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])

    def test_after_1_sync(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_after': False}

        @events.after
        def method_with_after():
            self.assertFalse(listeners_called['listener_1'])
            self.assertFalse(listeners_called['listener_2'])
            listeners_called['method_with_after'] = True
            return True

        def listener_1(result):
            listeners_called['listener_1'] = result

        def listener_2(result):
            listeners_called['listener_2'] = result

        method_with_after += listener_1
        method_with_after += listener_2
        method_with_after(run_async=False)

        self.assertTrue(listeners_called['method_with_after'])
        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])

    def test_after_2(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_after': False}

        @events.after
        def method_with_after():
            listeners_called['method_with_after'] = True
            return True

        e1 = threading.Event()

        def listener_1(result):
            listeners_called['listener_1'] = result
            e1.set()

        e2 = threading.Event()

        def listener_2(result):
            listeners_called['listener_2'] = result
            e2.set()

        method_with_after += [listener_1, listener_2]
        method_with_after()

        e1.wait()
        e2.wait()

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertTrue(listeners_called['method_with_after'])

    def test_source_combination(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_before': False}

        listeners = list()

        @events.before
        def method_with_before():
            self.assertTrue(listeners_called['listener_1'])
            self.assertTrue(listeners_called['listener_2'])
            listeners_called['method_with_before'] = True

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

        self.assertEqual(len(listeners), 1)
        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertTrue(listeners_called['method_with_before'])

    def test_multiple_lists(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_before': False}

        @events.before
        def method_with_before():
            self.assertTrue(listeners_called['listener_1'])
            self.assertTrue(listeners_called['listener_2'])
            listeners_called['method_with_before'] = True

        def listener_1():
            listeners_called['listener_1'] = True

        def listener_2():
            listeners_called['listener_2'] = True

        method_with_before += listener_1
        method_with_before += [listener_2]
        method_with_before()

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertTrue(listeners_called['method_with_before'])

    def test_remove_listeners(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'listener_3': False, 'listener_4': False, 'method_with_before': False}

        @events.before
        def method_with_before():
            self.assertFalse(listeners_called['listener_1'])
            self.assertTrue(listeners_called['listener_2'])
            self.assertFalse(listeners_called['listener_3'])
            self.assertTrue(listeners_called['listener_4'])
            listeners_called['method_with_before'] = True

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

        self.assertFalse(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertFalse(listeners_called['listener_3'])
        self.assertTrue(listeners_called['listener_4'])
        self.assertTrue(listeners_called['method_with_before'])

    def test_multiple_classes(self):
        class Subject(object):
            def __init__(self):
                self.counter = 0

            @events.before
            def on_stuff(self):
                pass

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

        self.assertEqual(len(handler_1_calls), 1)
        self.assertEqual(len(handler_2_calls), 1)

    def test_listeners(self):
        listeners = events.AsyncListeners()

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
        listeners = events.AsyncListeners()

        entries = {'function': 0, 'function_1': 0, 'function_2': 0}

        @events.after
        def function():
            entries['function'] += 1

        function += listeners

        @events.after
        def function_1(param=None):
            entries['function_1'] += 1

        function_1 += listeners
        listeners += function_1

        @events.after
        def function_2(param=None):
            entries['function_2'] += 1

        function_2 += listeners
        listeners += function_2

        function(run_async=False)
        function_1(run_async=False)
        function_2(run_async=False)

        self.assertEqual(entries['function'], 1)
        self.assertEqual(entries['function_1'], 3)
        self.assertEqual(entries['function_2'], 3)

    def test_composite_result(self):
        @events.after
        def function():
            return events.CompositeEvent([1, 2])

        listener_calls = {'calls': 0}

        def listener(x):
            listener_calls['calls'] += 1

        function += listener

        function(run_async=False)

        self.assertEqual(listener_calls['calls'], 2)

    def test_automatic_linking(self):
        events.use_global_event_bus()
        listeners_called = {'listener_1': False, 'listener_2': False, 'listener_3': False, 'listener_4': False, 'listener_5': False, 'method_with_before': False}

        @events.before
        def method_with_before(x):
            self.assertTrue(listeners_called['listener_1'])
            self.assertTrue(listeners_called['listener_2'])
            listeners_called['method_with_before'] = x

        @events.listener
        def listener_1(x):
            listeners_called['listener_1'] = x

        @events.listener
        def listener_2(x):
            listeners_called['listener_2'] = x

        class Test(object, metaclass=events.GlobalRegister):

            @staticmethod
            @events.listener
            def static_test(x):
                listeners_called['listener_3'] = x

            @events.listener
            def method_test(self, x):
                listeners_called['listener_4'] = x

            @events.listener
            def method_test_2(self, x):
                listeners_called['listener_5'] = x

        Test()

        events.use_global_event_bus()

        method_with_before(True)

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertTrue(listeners_called['listener_3'])
        self.assertTrue(listeners_called['listener_4'])
        self.assertTrue(listeners_called['listener_5'])
        self.assertTrue(listeners_called['method_with_before'])


if __name__ == '__main__':
    unittest.main()
