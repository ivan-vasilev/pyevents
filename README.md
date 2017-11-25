# Lightweight Asynchronous Events For Python

Lightweight async events python library with decorators. There are two modes of operation - local and global

### Local
This is the default mode. You can add **before** and **after** listeners to event providers manually. Here is how it works with **before**:

```python
import pyevents.events as events

@events.before
def function_with_before(x):
    print('function_with_before called with argument: ' + x)

def listener_1(x):
    print('listener_1 called with argument: ' + x)

def listener_2(x):
    print('listener_2 called with argument: ' + x)

function_with_before += listener_1
function_with_before += listener_2
```
So when you call:
```python 
>>> function_with_before('argument')
listener_1 called with argument: argument
listener_2 called with argument: argument
function_with_before called with argument: argument
```

Conversely, you can use **after**: 


```python 
import pyevents.events as events

@events.after
def function_with_after(x):
    print('function_with_after called with argument: ' + x)
    return 'success'

def listener_1(result):
    print('listener_1 called with argument: ' + result)

def listener_2(result):
    print('listener_2 called with argument: ' + result)

function_with_after += listener_1
function_with_after += listener_2
```

And the result will be:
```python 
>>> function_with_after('argument')
function_with_after called with argument: argument
listener_1 called with argument: success
listener_2 called with argument: success
```
Please keep in mind that the _after_ decorator is asynchronous.

### Global
If you aim at fully event driven architecture, it will become tedious to maintain all the provider/listener connections. To help you with this the library supports global mode, where **all** event providers and listeners share the same global event bus by default. If you use global mode the previous example becomes:

```python 
import pyevents.events as events

events.use_global_event_bus()

@events.after
def function_with_after(x):
    print('function_with_after called with argument: ' + x)
    return 'success'

@events.listener
def listener_1(result):
    print('listener_1 called with argument: ' + result)

@events.listener
def listener_2(result):
    print('listener_2 called with argument: ' + result)


>>> function_with_after('argument')
function_with_after called with argument: argument
listener_1 called with argument: success
listener_2 called with argument: success
```

This is the gist of it. There are some more use cases in the unit tests.

#### Author
Ivan Vasilev (ivanvasilev [at] gmail (dot) com)

#### License
[MIT License](http://opensource.org/licenses/MIT)