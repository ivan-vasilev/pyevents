import unittest
import pyevents.events as events
import threading


class TestEvents(unittest.TestCase):
    """
    Test events
    """

    def test_1_sync(self):
        listeners_called = {'listener_1': False, 'listener_2': False}

        listeners = events.SyncListeners()

        def listener_1(x):
            listeners_called['listener_1'] = x

        def listener_2(x):
            listeners_called['listener_2'] = x

        listeners += listener_1
        listeners += listener_2
        listeners(True)

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])

    def test_2_async(self):
        listeners_called = {'listener_1': False, 'listener_2': False}

        listeners = events.AsyncListeners()

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

    def test_multiple_lists(self):
        listeners_called = {'listener_1': False, 'listener_2': False}

        listeners = events.SyncListeners()

        def listener_1():
            listeners_called['listener_1'] = True

        def listener_2():
            listeners_called['listener_2'] = True

        listeners += listener_1
        listeners += [listener_2]
        listeners()

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])

    def test_multiple_lists_async(self):
        listeners_called = {'listener_1': False, 'listener_2': False}

        listeners = events.SyncListeners()

        e1 = threading.Event()

        def listener_1():
            listeners_called['listener_1'] = True
            e1.set()

        e2 = threading.Event()

        def listener_2():
            listeners_called['listener_2'] = True
            e2.set()

        listeners += listener_1
        listeners += [listener_2]
        listeners()

        e1.wait()
        e2.wait()

        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])

    def test_remove_listeners(self):
        listeners_called = {'listener_1': False, 'listener_2': False, 'listener_3': False, 'listener_4': False}

        listeners = events.SyncListeners()

        def listener_1():
            listeners_called['listener_1'] = True

        def listener_2():
            listeners_called['listener_2'] = True

        def listener_3():
            listeners_called['listener_2'] = True

        def listener_4():
            listeners_called['listener_4'] = True

        listeners += listener_1
        listeners += listener_2

        listener_3_list = [listener_3]
        listeners += listener_3_list
        listeners += [listener_4]

        listeners -= listener_1
        listeners -= listener_3_list

        listeners()

        self.assertFalse(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])
        self.assertFalse(listeners_called['listener_3'])
        self.assertTrue(listeners_called['listener_4'])

    def test_source_combination(self):
        listeners_called = {'listener_1': False, 'listener_2': False}

        listeners = events.AsyncListeners()

        def listener_1():
            self.assertFalse(listeners_called['listener_1'])
            listeners_called['listener_1'] = True

        def listener_2():
            self.assertFalse(listeners_called['listener_2'])
            listeners_called['listener_2'] = True

        listeners += listener_1
        listeners += listeners
        listeners += listener_2
        listeners()

        self.assertEqual(len(listeners), 1)
        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])


if __name__ == '__main__':
    unittest.main()
