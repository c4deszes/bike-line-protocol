Code generator
==============

The library includes a code generator, it's written in Python and it generates the application code
for specific nodes. When integrated right the node will answer to the incoming transport requests
with the right signal values, and also it will listen to other nodes.

Commands
--------

Run either one of these commands, this will result in two files (``line_api.c``, ``line_api.h``) to
be generated in the output folder.

.. code-block:: bash

    python -m line_protocol.codegen <config> [--output <path>]

Options
-------

**<config>**: Path to the codegen config file

**--output**: Directory path where the generated code will be written, by default the current directory

Configuration
-------------

The codegen config is a JSON file that describes each transport channel, what nodes the codegen
should generate code for and their diagnostic settings.

Transport setup
~~~~~~~~~~~~~~~

Every transport channel must provide a name, a unique channel number and whether the channel will
be using one wire (bus) type communication. The network file path is relative to the config file.

.. code-block:: json

    {
        "Network1": {                                   // Transport channel name, must be unique
            "channel": 0,                               // Transport channel index, must be unique
            "oneWire": true,                            // Whether the transport channel operates on a shared RX/TX line
            "network": "path/to/network.json",          // Path to the network configuration

The transport channel can specify which nodes to generate code for, with that it's possible to
implement multiple nodes in the same physical ECU.

.. code-block:: json

            "nodes": {                                  // List of nodes that this ECU will implement, generally just one
                "FrontLight": {
                    "enabled": true,                    // General enable flag, when disabled the frames and diagnostics
                                                        // for the given node will be removed from the code
                    "diagnostics": {                    // Diagnostic control
                        "channel": 0                    // Diagnostic channel index, must be unique across the whole code config
                        "enabled": true                 // When disabled no diagnostic callouts will be performed
                        "initAddress": true             // When set to true the diagnostic address will be set after init
                                                        // when set to false the address won't be assigned
                                                        // when set to a number then that number will be assigned, but results in a warning
                        
                    }
                },
                "RearLight": {
                    "enabled": true
                }
            }
        }
    }
