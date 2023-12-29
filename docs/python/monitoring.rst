Monitoring
==========

The monitoring configuration is specificied in a JSON file, it references a network and extends it
with information like which signals the user wants to monitor.

Configuration
-------------

.. code-block:: json

    {
        "network": "network.json",
        "prestartSchedules": [
            "DumpNetworkInfo"
        ],
        "mainSchedule": "NormalSchedule",
        "plots": {
            "SpeedPlot": {
                "signals": [
                    "FrontSpeed",
                    "RearSpeed"
                ]
            }
        }
    }
