from .network import Network
from .request import FormulaEncoder, MappingEncoder, Request, Signal, NoneEncoder
from .nodes import Node

import json

def load_network(path: str) -> Network:
    with open(path, 'r') as f:
        data = json.load(f)

    network = Network(data['name'])

    for (name, enc) in data['encoders'].items():
        if enc['type'] == 'formula':
            network.encoders.append(FormulaEncoder(name, enc['scale'], enc['offset']))
        elif enc['type'] == 'mapping':
            network.encoders.append(MappingEncoder(name, enc['mapping']))
    
    for (name, req) in data['requests'].items():
        signals = []
        for (sig_name, sig) in req['layout'].items():
            try:
                encoder = network.get_encoder(sig['encoder'])
            except KeyError:
                encoder = NoneEncoder('none')

            signal = Signal(sig_name, sig['offset'], sig['width'], encoder)
            signals.append(signal)

        network.requests.append(Request(name, int(req['id'], base=0), int(req['size'], base=0), signals))

    for (name, nod) in data['nodes'].items():
        node = Node(name, int(nod['address'], base=0))
        node.publishes = [network.get_request(x) for x in nod['publishes']]
        node.subscribes = [network.get_request(x) for x in nod['subscribes']]
        network.nodes.append(node)

    return network
