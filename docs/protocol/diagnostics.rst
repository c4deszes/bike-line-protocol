Diagnostics
===========

Request codes
-------------

.. list-table::
    :header-rows: 1

    * - Category
      - First ID
      - Last ID

    * - Broadcast request
      - ``0x0000``
      - ``0x01FF``

    * - Unicast request
      - ``0x0200``
      - ``0x0FFF``

Broadcast requests address all peripherals, the data is provided by the master.

Unicast requests address a specific peripheral, the lowest nibble is used as the address.
``0x0`` and ``0xF`` are reserved, therefore 14 devices supporting unicast requests can be on the
same network.

Lifecycle operations
--------------------

Wakeup (empty request)
~~~~~~~~~~~~~~~~~~~~~~

The request code ``0x0000`` is used to wakeup all peripherals, it's an empty message with no
payload. Peripherals will in general wakeup on the line transitions, but it's important that
peripherals already awake still sense valid messages coming in.

Idle
~~~~~

The request code ``0x0100`` is used to send all peripherals into idle mode. This mode is selected
by the body computer when the bicycle is found to be idle. No payload is provided.

The peripheral is expected to continue operation when a wakeup is received, this also means that the
ride continues therefore attributes stored for a ride should be recalled, e.g.: distance.

The peripheral's current consumption should be reduced.

In this mode the peripherals are allowed to initiate wakeup of the network by sending a break
``0x00``, for example a motion sensor could detect that the bike is in use again. This pulse can
wakeup other devices but more importantly the body computer which in turn can send the official
wakeup frame.

Shutdown
~~~~~~~~

The request code ``0x0101`` is used to shutdown all peripherals. This mode is selected by the body
computer when the ride ends by user request, the ignition switch is set to off or the battery is
removed. No payload is provided.

Addressing
----------

Each peripheral on a network stores it's diagnostic address, the address initially is unassigned
applications can then change it to whatever they have stored.

Conditional change address
~~~~~~~~~~~~~~~~~~~~~~~~~~

The request code ``0x01E0`` is used to setup nodes that don't yet have a diagnostic address. The
request data starts with a serial number followed by the new address.

Nodes that already use the address but don't match in serial number must unassign their address to
avoid conflicts.

.. kroki::
    :type: packetdiag

    packetdiag {
        colwidth = 8;
        node_height = 36;

        0-31: Serial number;
        32-39: New diagnostic address;
    }

Internal states
---------------

Get operation status
~~~~~~~~~~~~~~~~~~~~

**Mandatory**

Returns the peripheral's status, which is just an overview whether the device has any issues or
everything is working as expected.

The following states shall be reported back:

.. list-table::
    :header-rows: 1

    * - Name
      - Code
      - Description

    * - Initializing
      - 0x00
      - The device is stil setting itself up

    * - Operational
      - 0x01
      - The device is fully functional

    * - Warning
      - 0x02
      - When experiencing some malfunction but the reported signals are valid

    * - Error
      - 0x03
      - When experiencing major or multiple malfunctions

    * - Bootloader
      - 0x40
      - When in bootloader mode, awaiting further instructions

    * - Boot error
      - 0x41
      - The device is unable to run the application code

Request code is ``0x020X``, the response length is 1 byte.

.. kroki::
    :type: packetdiag

    packetdiag {
        colwidth = 8;
        node_height = 36;

        0-7: Status code (0x00-0xFF);
    }

Get power status
~~~~~~~~~~~~~~~~

Returns whether the current power conditions are sufficient for the peripheral's operation.

Also returns an estimated operating current used at the time of the request, an estimated or
theoretical peak operating current and the sleep mode current consumption. The former is used to
estimate battery life and the latter is used for compatibility and lastly the sleep current
indicates whether the battery is going to drain long term.

The response contains the following:

* Measured voltage by the peripheral
* Actual operating current of the peripheral in 1 mA/inc
* Sleep current of the peripheral in 1uA/inc

Request code is ``0x021X``, the response length is 4 bytes.

.. kroki::
    :type: packetdiag

    packetdiag {
        colwidth = 32;
        node_height = 36;

        0-7: U_measured;
        8-23: I_operating;
        24-31: I_sleep;
    }

Metainformation
---------------

Get Serial Number
~~~~~~~~~~~~~~~~~

**Mandatory**

Returns the serial number of the peripheral, the serial number is a 32bit integer.

Request code is ``0x022X``, the response length is 4 bytes.

.. kroki::
    :type: packetdiag

    packetdiag {
        colwidth = 32;
        node_height = 36;

        0-7: Serial LSB;
        8-15: ...;
        16-23: ...;
        24-31: Serial MSB;
    }

Get Software Version
~~~~~~~~~~~~~~~~~~~~

Returns the software version currently on the peripheral, the version is a semantic version stored
as 1 byte for each field major, minor, patch and one additional reserved byte for a total of 4 bytes
in length.

Request code is ``0x022X``, the response length is 4 bytes.

.. kroki::
    :type: packetdiag

    packetdiag {
        colwidth = 32;
        node_height = 36;

        0-7: Major;
        8-15: Minor;
        16-23: Patch;
        24-31: Reserved;
    }
