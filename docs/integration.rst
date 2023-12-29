Integration guide
=================

Physical and Transport layer
----------------------------

During the initialization of the program the transport layer should be initialized as well.
This sets the internal states to be ready receiving the first frame.

.. code-block:: c

    #include "line_transport.h"

    void Init() {
        LINE_Transport_Init();
    }

As data is being received from the physical layer the receive function should be called. How often
the receive function is called is important in making sure all requests are processed in time.

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

The protocol stack can be easily integrated into CMake projects using CPM or the ``add_subdirectory``
function call. Once included the library is available as an interface target and a function can be
used to generate C code for the application layer.

.. code-block:: cmake

    find_package(Python REQUIRED)

    include(tools/cmake/CPM.cmake)
    CPMAddPackage("gh:c4deszes/bike-line-protocol#feature/first-version")

    # This function creates the codegen target and an interface library
    # which includes all sources and includes
    line_codegen(
        TARGET protocol-stack-api       # Interface target name
        NETWORK config/network.json     # Path to the network configuration file
        NODE CustomPeripheral           # Node for which to generate the interface
        ADAPTER                         # When added it includes default adapters between
                                        # the application and transport layer
    )
    
    # You can then create a real target which inherits the interface's properties
    # The microcontroller specific compiler flags can be added to this target later
    add_library(protocol-stack STATIC)
    target_link_libraries(protocol-stack PUBLIC protocol-stack-api)

Arduino
-------

Because the library is not published yet the integration can only be done using ``arduino-cli``.
The library needs to be cloned, then code generation has to be called manually, afterwards the
compile command can be called with the additional library path.

.. code-block:: bash

    line-codegen network.json --output . --node Arduino
    arduino-cli compile -b <board> --library C:/workspace/bike-line-protocol --clean

.. note:: The solution relies on the fact that the Arduino library spec. simply takes all ``.c``
          files under the ``src`` folder and links them in the final binary.

.. note:: The ``--clean`` flag is recommended when changing library internals or network
          configuration, because the arduino tooling won't detect these files as having
          an effect on cache.
