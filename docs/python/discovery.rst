Discovery
=========

Discovers peripherals on a network.

Command
-------

.. code-block:: bash

    line-discovery --port COM3 --baudrate 9600 --no-info

Options
-------

**--no-info**: Disables retrival of information such as software version and serial number

Example
-------

.. code-block:: bash

    line-discovery --port COM3

.. code-block:: text

    Peripheral 0x1 - STATUS: ok - SW: 0.1.0 - SERIAL ABCDEF01
    Peripheral 0x2 - STATUS: ok - SW: 1.0.0 - SERIAL DEADBEEF
