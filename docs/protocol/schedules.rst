Schedules
=========

Scheduling is a crucial part of the communication protocol, it determines when requests are sent out
on the bus. This may affect how peripherals behave, how fresh the data is and how much bus load there is.

Definitions
-----------

**Slot**: a slot is a time interval on the bus where a request might be sent and a response may be received

**Order**: determines the type of order in which requests are sent, this can be fixed, random or something more dynamic

**Slotting**: determines how slots are allocated, this can be a fixed period and length, a delay between slots or something else

Ordering types
--------------

**Fixed order** means that the requests are sent in a predetermined order, one after another. The
same request may be sent multiple times in a row to emulate a higher priority for that request.

**Dynamic order** means that the requests are sent in a non-deterministic order, based on some
criteria. This can be based on request priority, time since last sent or randomization.

Slotting types
--------------

**Fixed slotting** means that slots are allocated at fixed intervals, with a predetermined length.
This can be used to ensure that requests are sent at regular intervals. The minimum slot length in
this case is determined by the longest request-response time.

**Dynamic slotting** means that slots end as the response is received. In case of a timeout the slot
also ends immediately. The next slot starts after an interframe delay has elapsed.
