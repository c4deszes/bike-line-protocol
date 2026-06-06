# pylint: disable=missing-function-docstring, missing-class-docstring, missing-module-docstring
# pylint: disable=invalid-name
import pytest
import time

from line_protocol.network import load_network
from line_protocol.network.request import SignalValueContainer
from line_protocol.protocol.master import LineMaster, LineTransportTimeout, RequestListener, NodeStatusListener, NodeStatusProperty
from line_protocol.protocol.simulation import SimulatedPeripheral
from unittest.mock import Mock

class TestLineMaster_VirtualBus_Raw:

    # No nodes, do transmit, do requests
    @pytest.fixture()
    def master(self):
        with LineMaster() as master:
            yield master

    def test_TransmitRequest_NoWait(self, master):
        master.send_request(0x1000, [0x02, 0x03])

    def test_TransmitRequest_Wait(self, master):
        master.send_request(0x1000, [0x02, 0x03], wait=True, timeout=1)

    def test_ReceiveResponse_NoWait(self, master):
        master.request(0x1000, wait=False)

    def test_ReceiveResponse_Wait(self, master):
        with pytest.raises(LineTransportTimeout):
            master.request(0x1000, wait=True, timeout=1)

class TestLineMaster_VirtualBus_Network:

    @pytest.fixture()
    def network(self):
        yield load_network('tests/data/network-1.json')

    @pytest.fixture()
    def peripheral(self, network):
        peripheral = SimulatedPeripheral(network.get_node('RotorSensor'))
        peripheral.op_status = 'Ok'
        peripheral.software_version = '1.0.0'
        peripheral.serial_number = 0x12345678
        yield peripheral

    @pytest.fixture()
    def master(self, network, peripheral):
        with LineMaster(network=network) as master:
            master.virtual_bus.add(peripheral)
            yield master

    def test_ReceiveRequest_NoWait(self, master, peripheral):
        peripheral.connected = True
        master.request("WheelSpeed", wait=False)

    def test_ReceiveRequest_Wait(self, master, peripheral):
        peripheral.connected = True
        response = master.request("WheelSpeed", wait=True, timeout=1)

        assert len(response) == 5

    def test_ReceiveRequest_Wait_Timeout(self, master, peripheral):
        peripheral.connected = False
        with pytest.raises(LineTransportTimeout):
            master.request("WheelSpeed", wait=True, timeout=0.1)

class TestLineMaster_VirtualBus_Diagnostics:

    @pytest.fixture()
    def network(self):
        yield load_network('tests/data/network-1.json')

    @pytest.fixture()
    def master(self, network):
        with LineMaster(network=network) as master:
            peripheral = SimulatedPeripheral(network.get_node('RotorSensor'))
            peripheral.op_status = 'Ok'
            peripheral.software_version = '1.0.0'
            peripheral.serial_number = 0x12345678
            #peripheral.power_status 
            master.virtual_bus.add(peripheral)
            yield master

    def test_Idle_NoWait(self, master):
        master.idle()

    def test_Idle_Wait(self, master):
        master.idle(wait=True, timeout=1)

    def test_Shutdown_NoWait(self, master):
        master.shutdown()

    def test_Shutdown_Wait(self, master):
        master.shutdown(wait=True, timeout=1)

    def test_GetOperationStatusByAddress_NoWait(self, master):
        assert master.get_node_status(0x01).op_status == None

        master.get_operation_status(node=0x01, wait=False)
        time.sleep(0.5)
        assert master.get_node_status('RotorSensor').op_status == 'Ok'

    def test_GetOperationStatusByName_Wait(self, master):
        status = master.get_operation_status(node='RotorSensor', wait=True, timeout=1)
        assert status == 'Ok'

    def test_GetSoftwareVersionByAddress_NoWait(self, master):
        assert master.get_node_status(0x01).software_version == None

        master.get_software_version(node=0x01, wait=False)
        time.sleep(0.5)
        assert master.get_node_status('RotorSensor').software_version == '1.0.0'

    def test_GetSoftwareVersionByName_Wait(self, master):
        version = master.get_software_version(node='RotorSensor', wait=True, timeout=1)
        assert version == '1.0.0'

    def test_GetSerialNumberByAddress_NoWait(self, master):
        assert master.get_node_status(0x01).serial_number == None

        master.get_serial_number(node=0x01, wait=False)
        time.sleep(0.5)
        assert master.get_node_status('RotorSensor').serial_number == 0x12345678

    def test_GetSerialNumberByName_Wait(self, master):
        serial_number = master.get_serial_number(node='RotorSensor', wait=True, timeout=1)
        assert serial_number == 0x12345678

class TestLineMaster_VirtualBus_Scheduling:
    @pytest.fixture()
    def network(self):
        yield load_network('tests/data/network-1.json')

    @pytest.fixture()
    def master(self, network):
        with LineMaster(network=network) as master:
            peripheral = SimulatedPeripheral(network.get_node('RotorSensor'))
            master.virtual_bus.add(peripheral)
            yield master

    def test_EnableSchedule(self, master):
        master.enable_schedule("RotorSensorSchedule")
        time.sleep(5)
        master.disable_schedule()

class TestLineMaster_VirtualBus_Listeners:

    @pytest.fixture()
    def network(self):
        yield load_network('tests/data/network-1.json')

    @pytest.fixture()
    def peripheral(self, network):
        peripheral = SimulatedPeripheral(network.get_node('RotorSensor'))
        peripheral.op_status = 'Ok'
        peripheral.software_version = '1.0.0'
        peripheral.serial_number = 0x12345678
        yield peripheral

    @pytest.fixture()
    def node_status_listener(self):
        yield Mock(spec=NodeStatusListener)

    @pytest.fixture()
    def request_listener(self):
        yield Mock(spec=RequestListener)

    @pytest.fixture()
    def master(self, network, node_status_listener, request_listener, peripheral):
        with LineMaster(network=network) as master:
            master.virtual_bus.add(peripheral)
            master.add_node_status_listener(node_status_listener)
            master.add_request_listener(request_listener)
            yield master

    def test_NodeStatusListener_OperationStatus(self, master, node_status_listener):
        master.get_operation_status(node='RotorSensor', wait=True, timeout=1)
        
        assert node_status_listener.on_node_change.called
        assert node_status_listener.on_node_change.call_args.args[1].address == 0x01
        assert node_status_listener.on_node_change.call_args.args[1].name == 'RotorSensor'
        assert node_status_listener.on_node_change.call_args.args[2].op_status == 'Ok'
        assert node_status_listener.on_node_change.call_args.args[3] == NodeStatusProperty.OP_STATUS

    def test_NodeStatusListener_SoftwareVersion(self, master, node_status_listener):
        master.get_software_version(node='RotorSensor', wait=True, timeout=1)

        assert node_status_listener.on_node_change.called
        assert node_status_listener.on_node_change.call_args.args[1].address == 0x01
        assert node_status_listener.on_node_change.call_args.args[1].name == 'RotorSensor'
        assert node_status_listener.on_node_change.call_args.args[2].software_version == '1.0.0'
        assert node_status_listener.on_node_change.call_args.args[3] == NodeStatusProperty.SOFTWARE_VERSION

    def test_NodeStatusListener_SerialNumber(self, master, node_status_listener):
        master.get_serial_number(node='RotorSensor', wait=True, timeout=1)

        assert node_status_listener.on_node_change.called
        assert node_status_listener.on_node_change.call_args.args[1].address == 0x01
        assert node_status_listener.on_node_change.call_args.args[1].name == 'RotorSensor'
        assert node_status_listener.on_node_change.call_args.args[2].serial_number == 0x12345678
        assert node_status_listener.on_node_change.call_args.args[3] == NodeStatusProperty.SERIAL_NUMBER

    def test_RequestListener(self, master, network, request_listener, peripheral):
        peripheral.connected = True
        peripheral.requests.WheelSpeed.FrontSpeed = 15
        peripheral.requests.WheelSpeed.RearSpeed = 14
        master.request("WheelSpeed", wait=True, timeout=1)

        assert request_listener.on_user_request.called
        assert isinstance(request_listener.on_user_request.call_args.args[0], float)
        assert request_listener.on_user_request.call_args.args[1] == master.network.get_request('WheelSpeed')
        assert isinstance(request_listener.on_user_request.call_args.args[2], list)
        assert len(request_listener.on_user_request.call_args.args[2]) == network.get_request('WheelSpeed').size
        #assert request_listener.on_user_request.call_args.args[2] == master.
        assert isinstance(request_listener.on_user_request.call_args.args[3], SignalValueContainer)
        assert request_listener.on_user_request.call_args.args[3].get_signal('FrontSpeed').phy -15 < 0.1
