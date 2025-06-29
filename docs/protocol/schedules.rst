Schedules
=========

Definitions
-----------

Slot: a slot is a time interval on the bus where a request might be sent and a response is received

Order: determines the type of order in which requests are sent, this can be fixed, random or something more dynamic
Slotting: determines how slots are allocated, this can be a fixed period and length, a delay between slots or something else




Strategies
----------

* Fix ordered schedule
  Requests are sent one after another, the delay time between frames is fixed
  When requests are disabled their allocated time is kept free on the bus

* Dynamic ordered schedule
  Delay between frames is one value
  When requests are disabled their allocated time is simply skipped over

---

* Ordered schedule consists of a fixed set of requests being sent out by the master, in a fixed order.
  The same request might be sent twice in a row or there might be additional requests in between.

* Bucketed schedule consists of a fixed set of requests being sent out by the master in a somewhat
  deterministic order. For every available slot a counter is incremented for each request identifier,
  then for every request there's a threshold at which point the request 

* Randomized schedule consists of a fixet set of requests where the next request is chosen randomly
  but the probability of a request being chosen can be increased by it's relative occurance.

* Randomized-Min schedule is same as randomized however each request type can be assigned a minimum
  period value, if the minimum would be violated the next request will be that instead of a random one.


