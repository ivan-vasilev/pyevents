# Lightweight Asynchronous Events For Python

Lightweight async events python library with decorators. There 2 modes of operation - local and global

## Local
This is the default mode. You can add **before** and **after** listeners to event providers manually. Here is how it works with before:

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
So when we call:
```python 
>>> method_with_before()
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
>>> method_with_after()
function_with_after called with argument: argument
listener_1 called with argument: success
listener_2 called with argument: success
```
Please keep in mind that the _after_ decorator is asynchronous 