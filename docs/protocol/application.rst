LINE Application layer
======================

Request codes
-------------

Codes are generally open to be used by peripherals, listening to all requests is also allowed,
however response should be restricted to a single peripheral on the network.

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
