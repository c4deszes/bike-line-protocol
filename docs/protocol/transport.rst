Protocol transport layer
========================

Describes how messages between the body computer and the peripherals are formatted.

Layout
------

.. kroki::
    :type: bytefield

    (def boxes-per-row 8)
    (draw-column-headers)
    (draw-box "Sync" {:span 1})
    (draw-box "Request" {:span 2})
    (draw-box "Size" {:span 1})
    (draw-gap "Payload")
    (draw-box nil :box-below)
    (draw-box "Checksum" {:span 1})
    (draw-bottom)

Sync
~~~~

Packets all start with a synchronization field, this can be used by the peripherals to synchronize
their clocks.

The sync field value is ``0x55`` which translates into an alternating bit sequence that can act as
a clock.

Request
~~~~~~~

The request identifies a function which is implemented by some peripheral, request codes are not
overlapping. Every peripheral will have it's own set of values that it can respond to.

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
bytes in the Request, Size and Payload fields, the calculation is offset by the constant ``0xA3``
