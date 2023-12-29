Transport layer
===============

Describes how messages between the body computer and the peripherals are formatted.

Layout
------

.. kroki::
    :type: packetdiag

    packetdiag {
        colwidth = 32;
        node_height = 36;

        0-7: Sync (0x55);
        8-9: Request parity;
        10-23: Request code;
        24-31: Payload size;
        32-87: Payload;
        88-95: Checksum;
    }

Sync
~~~~

Packets all start with a synchronization field, this can be used by the peripherals to synchronize
their clocks.

The sync field value is ``0x55`` which translates into an alternating bit sequence that can act as
a clock.

Request
~~~~~~~

The request code identifies a function which is implemented by some peripheral, request codes are
not overlapping. Every peripheral will have it's own set of values that it can respond to, but
peripherals might listen to the same requests.

A 2 bit parity value is calculated based on the 14 bit request codes, 

Size
~~~~

Size tells each peripheral how long the incoming or outbound message should be.

Payload
~~~~~~~

Payload is the data that's sent or received by the body computer, it's length shall match the
the size field's value. This means that the maximum permitted payload size is ``255`` bytes.

Checksum
~~~~~~~~

Checksum is used to validate that the message was not disturbed. It's calculated as the sum of all
bytes in the Size and Payload fields, the calculation is offset by the constant ``0xA3``.

Parity calculation
------------------

The 2 bits of parity in the request code are calculated separately.

The first bit is set to 1 if the number of 1's in the request code is odd.

The second bit is set to 1 if the number of 1's at the odd numbered bit positions is odd.

Example
~~~~~~~

.. code-block:: text

    requestCode = 0x0237 = 0010 0011 0111
    parityBit1 = 0010 0011 0111
                   ^    ^^  ^^^ = 6 (even) -> 0
    parityBit2 = 001000110111
                  ^ ^ ^ ^ ^ ^ = 3 (odd) -> 1
    finalRequestCode = 0110 0011 0111
                       ^^

Pseudocode
~~~~~~~~~~

.. code-block:: text

    function (request) -> {
        parity1 = 0;
        tempData = request;
        while (tempData != 0) {
            parity1 = parity1 ^ (tempData & 1);
            tempData = tempData >> 1;
        }

        parity2 = 0;
        tempData = request;
        for (int i = 0; i < 6; i++) {
            parity2 = parity2 ^ (tempData & 1);
            tempData = tempData >> 2;
        }

        return (((parity1 << 1) | parity2) << 14) | request;
    }
