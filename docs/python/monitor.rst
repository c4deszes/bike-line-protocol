Monitor
=======

Monitoring tools allow listening to live bus traffic, decoding signals and dumping the logs.

Command
-------

Performs a schedule and logs data according to the configuration.

.. code-block:: bash

    line-monitor <config> --port <port> [--master] [--dump-traffic <path>] [--dump-signals <path>]

Options
-------

**<config>**: Configuration file to use

**--port**: Serial port to use

**--master**: When set the tool will act as the master, performing the schedules set in the configuration,
              otherwise the tool listens on the network and decodes the requests

**--dump-traffic**: When enabled the traffic will be recorded and a file will be written

**--dump-signals**: When enabled the signals will be recorded and a file will be written

Configuration
-------------

The monitoring configuration is specificied in a JSON file, it references a network and extends it
with information like which signals the user wants to monitor.

The network path is relative to the configuration file.

The prestart schedules are called when the master starts communication, afterwards the main schedule
is called in a loop until the program exits.

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
                    "SpeedStatus.FrontSpeed",
                    "SpeedStatus.RearSpeed"
                ]
            }
        }
    }

Logging
-------

Uncompressed traffic
--------------------

Used by PC based logging software, every entry has a timestamp relative to the start time.
Entries are either complete requests with data or requests with an error message like timeout, crc
or header error.

.. code-block:: json

    {
        "logs": [
            {"timestamp": 1704012070.081624, "request": 513, "size": 1, "data": [0], "checksum": 164},
            {"timestamp": 1704012073.8413775, "request": 4097, "size": 8, "data": [0, 0, 0, 0, 0, 0, 0, 0], "checksum": 171},
            {"timestamp": 1704012074.4145166, "request": 545, "error": "timeout"}
        ]
    }

Compressed traffic
------------------

Used by embedded controllers, log begins with a starting timestamp (32bit), this is followed by the
records. Each record starts with a timestamp relative to the starting timestamp (32bit), followed by
the request code (16bit), the data length (8bit), data (variable) and lastly the checksum (8bit).

Errors are logged by setting the parity bits in the request code, this is followed by a data length,
then finally the data. The data is usually an error code, but it may contain partial data, etc.

.. code-block:: text

    1704012074

    0           0x2000 4 0x00 0x00 0x00 0x00 0xAF
    134         0x2080 2 0xAB 0xCD 0x46
    578         0x2000 4 0x00 0x00 0x00 0x00 0xAF
    1371        0xC205 1 0x02
