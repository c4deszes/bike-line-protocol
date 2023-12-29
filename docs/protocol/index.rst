Communication stack
===================

.. toctree::

    physical
    transport
    application
    diagnostics

The communication stack consists of:

* Physical layer: the way symbols (bytes) are transported
* Transport layer: the way sequences of symbols are interpreted
* Application and diagnostic layer: the way contents of entire messages are interpreted

The integrator is responsible for:

* Connecting the physical layer to the transport layer's receive port
* Proper timing of the transport layer calls
* Connecting the application layer to the transport layer if necessary
