Application layer
=================

Request codes
-------------

Codes are generally open to be used by peripherals, listening to all requests is also allowed,
however response should be restricted to a single peripheral on the network to prevent collisions.

.. list-table::
    :header-rows: 1

    * - Category
      - First ID
      - Last ID

    * - Diagnostic requests
      - ``0x0000``
      - ``0x0FFF``

    * - Application specific requests
      - ``0x1000``
      - ``0x2000``

    * - Reserved
      - ``0x2000``
      - ``0x3FFF``

Signals
-------

The provided code generator creates an application interface that uses signals as a way of back and
forth communication, the master will respond to it's own requests with signals, peripherals can
listen to these and perform actions accordingly. Peripherals can then publish their own signals so
the master can monitor them.

Layout
~~~~~~

The current code generator used C bitfields to pack signals and on the Python library side ``c_types``
is used to pack and unpack data.

This might be changed later due to possible inconsistencies between platforms.
