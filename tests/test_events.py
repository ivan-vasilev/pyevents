import threading
import unittest

import pyevents.events as events


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

        listeners = events.SyncListeners()

        def listener_1():
            self.assertFalse(listeners_called['listener_1'])
            listeners_called['listener_1'] = True

        def listener_2():
            self.assertFalse(listeners_called['listener_2'])
            listeners_called['listener_2'] = True

        listeners += listener_1
        listeners += listener_2
        listeners()

        self.assertEqual(len(listeners), 2)
        self.assertTrue(listeners_called['listener_1'])
        self.assertTrue(listeners_called['listener_2'])

    def test_sequence(self):
        data = {'value': 0}

        listeners = events.SyncListeners()

        def listener_1(d):
            self.assertEqual(d['value'], 0)
            d['value'] = 1

        def listener_2(d):
            self.assertEqual(d['value'], 1)
            d['value'] = 2

        listeners += listener_1
        listeners += listener_2
        listeners(data)

        self.assertEqual(data['value'], 2)

    def test_event_filter(self):
        data = {'listener_1_calls': 0, 'listener_2_calls': 0}

        listeners = events.SyncListeners()

        def listener_1(d):
            data['listener_1_calls'] += 1
            self.assertNotEqual(d, 'transformed')

        listeners += listener_1

        def listener_2(d):
            data['listener_2_calls'] += 1
            self.assertEqual(d, 'transformed')

        ef = events.EventFilter(listeners,
                                event_filter=lambda x: x == 'all_listeners',
                                event_transformer=lambda x: ('transformed',))
        ef += listener_2

        listeners('listener_1_only')
        listeners('all_listeners')

        self.assertEqual(data['listener_1_calls'], 2)
        self.assertEqual(data['listener_2_calls'], 1)

    def test_event_filter_2(self):
        calls_count = {'listener_1_calls': 0, 'listener_2_calls': 0, 'listener_3_calls': 0}

        listeners = events.SyncListeners()

        def listener_1(d):
            calls_count['listener_1_calls'] += 1

        listeners += listener_1

        def listener_2(d):
            calls_count['listener_2_calls'] += 1
            self.assertEqual(d['data'], 'transformed')

        ef = events.EventFilter(listeners,
                                event_filter=lambda x: x['type'] == 'all_listeners',
                                event_transformer=lambda x: ({**x, **{'data': 'transformed'}}, ))
        ef += listener_2

        def listener_3(d):
            calls_count['listener_3_calls'] += 1
            self.assertEqual(d['data'], 'transformed')

        child_ef = ef.filter_and_transform(event_filter=lambda x: True if x['type'] == 'all_listeners' and 'additional_condition' in x else False,
                                           event_transformer=lambda x: ({**x, **{'data': x['data']}}, ))

        child_ef += listener_3

        listeners({'type': 'listener_1_only'})
        listeners({'type': 'all_listeners'})

        self.assertEqual(calls_count['listener_1_calls'], 2)
        self.assertEqual(calls_count['listener_2_calls'], 1)
        self.assertEqual(calls_count['listener_3_calls'], 0)

        listeners({'type': 'all_listeners', 'additional_condition': True})

        self.assertEqual(calls_count['listener_1_calls'], 3)
        self.assertEqual(calls_count['listener_2_calls'], 2)
        self.assertEqual(calls_count['listener_3_calls'], 1)


if __name__ == '__main__':
    unittest.main()
