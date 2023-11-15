import os
from line_protocol.network import load_network

class TestNetworkLoad:

    def test_LoadNetwork_1(self):
        path = os.path.join(os.path.dirname(__file__), 'data', 'network-1.json')
        network = load_network(path)

        # Nodes
        assert len(network.nodes) == 2

        node = network.get_node('BodyComputer')
        assert node.address == 0x00
        assert node.subcribes[0] == network.get_request('WheelSpeed')

        node = network.get_node('RotorSensor')
        assert node.address == 0x01
        assert node.publishes[0] == network.get_request('WheelSpeed')

        # Requests
        request = network.get_request('WheelSpeed')
        assert request.id == 0x1000
        assert request.size == 5

        # Encoders
        assert len(network.encoders) == 2


