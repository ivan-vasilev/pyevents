import unittest
from pyevents.events import *


class EventsTest(unittest.TestCase):
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

        method_with_before += listener_1
        method_with_before += listener_2
        method_with_before(True)

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertTrue(listeners_called['method_with_before'])

    def test_before_2(self):

        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_before': False}

        class TestClass(object):

            @before
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

    def test_after_1(self):

        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_after': False}

        @after
        def method_with_after():
            self.assertFalse(listeners_called['listener_1'])
            self.assertFalse(listeners_called['listener_2'])
            listeners_called['method_with_after'] = True

        def listener_1():
            listeners_called['listener_1'] = True

        def listener_2():
            listeners_called['listener_2'] = True

        method_with_after += listener_1
        method_with_after += listener_2
        method_with_after()

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertTrue(listeners_called['method_with_after'])

    def test_after_2(self):

        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_after': False}

        @after
        def method_with_after():
            self.assertFalse(listeners_called['listener_1'])
            self.assertFalse(listeners_called['listener_2'])
            listeners_called['method_with_after'] = True

        def listener_1():
            listeners_called['listener_1'] = True

        def listener_2():
            listeners_called['listener_2'] = True

        listeners = [listener_1, listener_2]
        method_with_after += listeners
        method_with_after()

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertTrue(listeners_called['method_with_after'])

    def test_source_combination(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'method_with_before': False}

        listeners = list()

        @before
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

        @before
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

        @before
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

            @before
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


if __name__ == '__main__':
    unittest.main()
