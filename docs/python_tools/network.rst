Network
=======

The network specification can be created using a JSON file.

Header
------

Network has a name and a baudrate setting.

.. code-block:: JSON

    {
        "name": "network1",
        "baudrate": 19200
    }

Nodes
-----

Each node has an address and requests that it publishes or subscribes to.

.. code-block:: json

    "RotorSensor": {
        "address": "0x1",
        "subscribes": [],
        "publishes": [
            "WheelSpeed"
        ]
    }

Requests
--------

Requests have a unique identifier, size and the signals.

The request shall fit all it's signals, gaps left in there will be padded.

When an encoder is not set the signal will always be encoded and decoded in raw format.

When an initial value and an encoder is provided the value is assumed to be in it's physical format.
If the encoder is not set the initial value is used as a raw value and by the default the initial
value is 0.

.. code-block:: json

    "WheelSpeed": {
        "id": "0x1000",
        "size": 4,
        "layout": {
            "FrontSpeed": {
                "offset": 0,
                "width": 16,
                "encoder": "SpeedEncoder",
                "initial": 0
            },
            "RearSpeed": {
                "offset": 16,
                "width": 16,
                "encoder": "SpeedEncoder",
                "initial": 0
            }
        }
    }

Encoder
-------

Encoders translate the data in between their network form and their system interpretation.

Formula
~~~~~~~

The formula encoder maps an integer range to a physical value range such as speed or angle. Notice
that this encoder has no limits so the signals entire range is considered valid.

.. code-block:: json

    "SpeedEncoder": {
        "type": "formula",
        "scale": 0.1,
        "offset": 10
    }

Mapping
~~~~~~~

The mapping encoder maps the integer values to an easily understandable string value, like an on/off
state or an enumeration.

.. code-block:: json

    "SpeedStatus": {
        "type": "mapping",
        "mapping": {
            "0": "Valid",
            "1": "Unreliable"
        }
    }

Schedules
---------

Schedules describe how the overall network traffic looks like over time, in it's simplest form a
schedule table specifies the requests to be sent by the master in order and the delay between those
requests.

.. code-block:: json

    "ConfigSchedule": {
        "delay": 0.1,
        "entries": [
            {"type": "request", "request": "SpeedStatus"},
            {"type": "wakeup"}
            {"type": "idle"},
            {"type": "shutdown"}
            {"type": "opstatus", "node": "RotorSensor"}
            {"type": "pwrstatus", "node": "RotorSensor"}
            {"type": "serial", "node": "RotorSensor"}
            {"type": "swversion", "node": "RotorSensor"}
        ]
    }

Two types of schedules are supported:

* Fixed: entries are executed in order, this is the default or when 'type' is set to 'fixed'.
* Priority aging: entries are executed based on their priority, when 'type' is set to 'priority-aging'.

Two types of slotting are supported:

* Variable: each entry is executed after the previous one plus the delay, this is the default or when 'slots' is set to 'variable'.
* Fixed: each entry is executed at fixed time intervals, when 'slots' is set to 'fixed'.

.. note:: Fixed slots are not supported at the moment.

Below is an example of a priority-aging schedule with variable slots. The priority and age parameters
are crucial for the schedule to work correctly. The age is used to prevent starvation, however even
that doesn't guarantee that low priority requests will always be sent.

.. code-block:: json

    "NormalSchedule": {
        "type": "priority-aging",
        "slots": "variable",
        "delay": 0.05,
        "entries": [
            {"type": "request", "request": "SpeedStatus", "priority": 2, "maxAge": 5},
            {"type": "request", "request": "LightSync", "priority": 4, "maxAge": 10},
        ]
    }
