Discovery
=========

Discovers peripherals on a network. The tool will act as a master on the bus and probes all
diagnostic addresses by requesting their operational status. When peripherals do respond the
tool optionally retrieves the software version, serial number and power status of the devices.

Command
-------

.. code-block:: bash

    line-discovery --port <port> [--baudrate <baud>] [--no-info]

Options
-------

**--port**: Serial port to use

**--baudrate**: Serial communication speed, defaults to 19200

**--network**: Path to the network file, optional

Example
-------

.. code-block:: bash

    line-discovery --port COM3

.. code-block:: text

    Peripheral 0x1 - STATUS: ok - SW: 0.1.0 - SERIAL ABCDEF01
    Peripheral 0x2 - STATUS: ok - SW: 1.0.0 - SERIAL DEADBEEF
