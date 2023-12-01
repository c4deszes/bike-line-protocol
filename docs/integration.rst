Integration guide
=================

Transport layer
---------------

During the initialization of the application the transport layer should be initialized as well.
This sets the internal states to be ready receiving the first frame.

.. code-block:: c

    #include "protocol/transport.h"

    void Init() {
        LINE_Transport_Init();
    }

As data is being received from the physical layer the receive function should be called.

.. code-block:: c

    void Task10ms() {
        int bytesAvailable = USART_HasData();
        while (bytesAvailable > 0) {
            LINE_Transport_Receive(USART_GetData());
        }
    }

There are three callback functions that are called once a frame is processed.

The request handler is called when the header part of a frame is received with valid parity. The
handler then needs to decide whether it's going to respond by returning ``true`` or ``false``.
The purpose of the return value is so the responding device can identify it's own message in the
data callback.

.. code-block:: c

    bool LINE_Transport_OnRequest(uint16_t request) {
        if (request == 0x0100) {
            LINE_Transport_WriteData();
            return true;
        }
        return false;
    }

The data handler is called when the data part of a frame is received with a valid checksum. The
handler would normally also be called with the data that's sent out by the device due to the
one-wire nature of the physical layer.

.. code-block:: c

    void LINE_Transport_OnData(bool response, uint16_t request, uint8_t size, uint8_t* payload) {
        if (response) {
            return;
        }
        
        if (request == 0x0FFF) {
            // Call diagnostic function
        }
    }

CMake using CPM/subdirectories
------------------------------

.. code-block:: cmake

    include(tools/cmake/CPM.cmake)
    CPMAddPackage("gh:c4deszes/bike-line-protocol#feature/first-version")

    # This function creates the codegen target and an interface library
    # which includes all sources and includes
    line_codegen(
        TARGET protocol-stack-api
        NETWORK config/network.json
        NODE CustomPeripheral
        ADAPTER
    )
    
    # You can then create a real target which inherits the interface's properties
    # The microcontroller specific 
    add_library(protocol-stack STATIC)
    target_link_libraries(protocol-stack PUBLIC protocol-stack-api)
