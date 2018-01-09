# Lightweight Asynchronous Events For Python

Extremely lightweight python events library. The goal is to have minimally intrusive interface. You don't need to implement and use any methods. You can just call the listeners object with the desired arguments to notify all subscribed listeners. You can add and remove listeners using the _+=_ and _-=_ operators. Here is an example: 

```python
import pyevents.events as events

listeners = events.SyncListeners() # alternatively you can use events.AsyncListeners() for async events

def listener_1(x):
    print("Listener 1 called with arguments: " + str(x))

def listener_2(x):
    print("Listener 2 called with arguments: " + str(x))

listeners += listener_1
listeners += listener_2
listeners('argument')

```
So when you call:
```python 
>>> listeners('argument')
Listener 1 called with arguments: argument
Listener 2 called with arguments: argument
```

That's the gist of it. There are a few other options, which you can see in the unit tests.

#### Author
Ivan Vasilev (ivanvasilev [at] gmail (dot) com)

#### License
[MIT License](http://opensource.org/licenses/MIT)