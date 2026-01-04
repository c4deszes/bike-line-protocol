Simulation
=================

The Python library includes ways to simulate peripherals which can be used for simulating the entire
system or even do restbus simulations where part of the bus is real hardware.

Peripheral implementation
-------------------------

.. code-block:: python

    from line_protocol.protocol.simulation import SimulatedPeripheral

    class MySimulatedPeripheral(SimulatedPeripheral):
        def __init__(self, node: Node):
            # The parent initialization must be called, this sets up the requests the peripheral
            # will respond to
            super().__init__(node)

            # Initialize your simulated peripheral here

        def on_subscriber_event(self, request: Request, signals: SignalValueContainer):
            # This method is called when a response is received for a request that this peripheral
            # is subscribed to. You can use this to update internal state or trigger other actions.
            pass

        def update(self, delta):
            # This is not a standard method, but you can implement your own update loop to simulate
            # behavior over time.

            # For example, you might want to change signal values based on elapsed time.
            self.requests.PeripheralStatus.Signal = 'NewValue'

            # Diagnostic properties can also be updated
            self.op_status = 'Ok'
            self.serial_number = 0x123456789
            self.software_version = '1.2.0'
            self.power_status.voltage = 12

        def on_wakeup(self):
            # Called when a wakeup request is received
            pass

        def on_idle(self):
            # Called when an idle request is received
            pass

        def on_shutdown(self):
            # Called when a shutdown request is received
            pass

        def on_conditional_change_address(self, old: int, new: int):
            # Called when the peripheral's address is changed
            pass

Simulation script
-----------------

The below example shows that the common `LineMaster` can be used with simulated peripherals, here
the physical bus is omitted and only the virtual bus is used.

.. code-block:: python

    from line_protocol.network import load_network
    from line_protocol.protocol.master import LineMaster
    from line_protocol.protocol.simulation import SimulatedPeripheral

    network = load_network('network-1.json')

    with LineMaster(network=network) as master:
        peripheral = SimulatedPeripheral(network.get_node('RotorSensor'))
        peripheral.op_status = 'Ok'
        peripheral.software_version = '1.0.0'
        peripheral.serial_number = 0x12345678

        master.virtual_bus.add(peripheral)

        master.enable_schedule("RotorSensorSchedule")
        time.sleep(5)
        master.disable_schedule()
