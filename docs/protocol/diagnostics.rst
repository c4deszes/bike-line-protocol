Diagnostic requests
===================

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
``0`` and ``0xF`` are reserved, therefore 14 devices supporting unicast requests can be on the
same network.

Lifecycle operations
--------------------

Wakeup (empty request)
~~~~~~~~~~~~~~~~~~~~~~

The request code ``0x0000`` is used to wakeup all peripherals, it's an empty message with no
payload. Peripherals will in general wakeup on the line transitions, but it's important that
peripherals already awake still sense valid messages coming in.

Sleep
~~~~~

The request code ``0x0100`` is used to send all peripherals into sleep mode. This mode is selected
by the body computer when the bicycle is found to be idle. No payload is provided.

Shutdown
~~~~~~~~

The request code ``0x0101`` is used to shutdown all peripherals. This mode is selected by the body
computer when the ride ends by user request, the ignition switch is set to off or the battery is
removed. A random integer byte is provided as payload, this code can be stored by the peripheral
and later might be recalled.

Internal states
---------------

Get operation status
~~~~~~~~~~~~~~~~~~~~

**Mandatory**

Returns the peripheral's status, which is just an overview whether the device has any issues or
everything is working as expected.

The following states shall be reported back:

* Ok: there's nothing wrong with the peripheral, all incoming and outgoing signals are valid
* Warning: the device is experiencing some malfunction but the reported signals are valid
* Error: the device is experiencing major or multiple malfunctions, the reported signals are unreliable

Request code is ``0x020X``, the response length is 1 byte.

Get power status
~~~~~~~~~~~~~~~~

**Mandatory**

Returns whether the current power conditions are sufficient for the peripheral's operation.

Also returns an estimated operating current used at the time of the request, an estimated or
theoretical peak operating current and the sleep mode current consumption. The former is used to
estimate battery life and the latter is used for compatibility and lastly the sleep current
indicates whether the battery is going to drain long term.

Power condition value contains:

* Voltage low/high/ok
* Brown out none/detected

Each current rating is provided as 1 byte in 25mA/inc scaling.

* 134 means 3.35A could be drawn by the peripheral

The sleep current is encoded differently as they are mostly sub-milliampere values, the scaling is
10uA/inc.

* 130 means 1.3mA is the peripheral's sleep current (which is quite high)

Request code is ``0x021X``, the response length is 4 bytes.

Metainformation
---------------

Get Serial Number
~~~~~~~~~~~~~~~~~

**Mandatory**

Get Software Version
~~~~~~~~~~~~~~~~~~~~

**Mandatory**
