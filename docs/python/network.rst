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

Each node has an address.

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

Requests have an identifier, size and the signals.

.. code-block:: json

    "WheelSpeed": {
        "id": "0x1000",
        "size": 4,
        "layout": {
            "FrontSpeed": {
                "offset": 0,
                "width": 16,
                "encoder": "SpeedEncoder"
            },
            "RearSpeed": {
                "offset": 16,
                "width": 16,
                "encoder": "SpeedEncoder"
            }
        }
    }

Encoder
-------

Formula
~~~~~~~

.. code-block:: json

    "SpeedEncoder": {
        "type": "formula",
        "scale": 0.1,
        "offset": 10
    }

Mapping
~~~~~~~

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

.. code-block:: json

    "ConfigSchedule": {
        "delay": "50 ms",
        "entries": [
            {"type": "request", "request": "SpeedStatus"},
            {"type": "wakeup"}
            {"type": "sleep"},
            {"type": "shutdown"}
            {"type": "opstatus", "node": "RotorSensor"}
            {"type": "pwrstatus", "node": "RotorSensor"}
            {"type": "serial", "node": "RotorSensor"}
            {"type": "swversion", "node": "RotorSensor"}
        ]
    }
