Command-line interface
======================

Code generator
--------------

Generates the application code based on the requests and signals defined in the network.

Run either one of these commands, this will result in two files (``line_api.c``, ``line_api.h``) to
be generated in the target folder.

.. code-block:: bash

    line-codegen network.json --node RotorSensor --output gencode/
    python -m line_protocol.codegen network.json --node RotorSensor --output gencode/

Monitor
-------

Performs a schedule and logs data according to the configuration.

.. code-block:: bash

    line-monitor config.json --port <port> [--master]

Options
~~~~~~~

**--port**: Serial port to use

**--config**: Configuration file to use

**--master**: When set the tool will act as the master, performing one of the schedules, otherwise
              the tool listens on the network and decodes the requests

Plotter
-------

Similar to the monitoring tool, but it plots the signal values in a GUI.

.. code-block:: bash

    line-plot config.json --port <port> [--master]
