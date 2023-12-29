Schedules
=========

Strategies
----------

* Ordered schedule consists of a fixed set of requests being sent out by the master, in a fixed order.
  The same request might be sent twice in a row or there might be additional requests in between.

* Randomized schedule consists of a fixet set of requests where the next request is chosen randomly
  but the probability of a request being chosen can be increased by it's relative occurance.

* Randomized-Min schedule is same as randomized however each request type can be assigned a minimum
  period value, if the minimum would be violated the next request will be that instead of a random one.
