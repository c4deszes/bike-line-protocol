Configuration
=============

The codegen config is a JSON file that describes each transport channel, what nodes the codegen
should generate code for and their diagnostic settings.

.. code-block:: json

    {
        "Network1": {                                   // Transport channel name, must be unique
            "channel": 0,                               // Transport channel index, must be unique
            "oneWire": true,                            // Whether the transport channel operates on a shared RX/TX line
            "network": "path/to/network.json",          // Path to the network configuration
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
