Integration guide
=================

Code integration
----------------

Below is the minimal code example to get the library working, this is assuming that an underlying
driver capable of sending and receiving bytes is present. Generally the transport layer would be
a serial port running at one of the standard frequencies.

When using the code generator only one function needs to be called during intialization, this takes
care of setting up the transport channels and diagnostics, all depending on configuration.

.. code-block:: c

    #include "line_protocol.h"
    #include "line_api.h"

    void Init() {
        LINE_App_Init();
    }

As data is being received from the physical layer the receive function should be called. How often
the receive function is called is important in making sure all requests are processed in time.

The transport channels also need a regular update call, this ensures that frames are timed out when
no response is received.

.. code-block:: c

    void Task1ms() {
        LINE_Transport_Update(transport_channel, 1);    // Update channel 0 time by 1ms

        int bytesAvailable = USART_HasData();
        while (bytesAvailable > 0) {
            LINE_Transport_Receive(transport_channel, USART_GetData());
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
    CPMAddPackage("gh:c4deszes/bike-line-protocol#master")

    # This function creates the codegen target and an interface library
    # which includes all sources and includes
    line_codegen(
        TARGET protocol-stack-api       # Interface target name
        CONFIG config/codegen.json      # Path to the configuration file
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

    line-codegen config.json --output .
    arduino-cli compile -b <board> --library C:/workspace/bike-line-protocol --clean

.. note:: The solution relies on the fact that the Arduino library spec. simply takes all ``.c``
          files under the ``src`` folder and links them in the final binary.

.. note:: The ``--clean`` flag is recommended when changing library internals or network
          configuration, because the arduino tooling won't detect these files as having
          an effect on cache.
