from .network import Network
from .request import FormulaEncoder, MappingEncoder, Request, Signal, NoneEncoder
from .nodes import Node
from typing import List
from .schedule import Schedule, RequestScheduleEntry, WakeupScheduleEntry, IdleScheduleEntry, ShutdownScheduleEntry, GetOperationStatusScheduleEntry, GetPowerStatusScheduleEntry, GetSerialNumberScheduleEntry, GetSoftwareVersionScheduleEntry

import json

def to_int(value: str) -> int:
    if isinstance(value, int):
        return value
    return int(value, base=0)

def load_schedules(network, obj: dict) -> List[Schedule]:
    schedules = []
    for (name, sche) in obj.items():
        entries = []
        for entry in sche['entries']:
            if entry['type'] == 'wakeup':
                entries.append(WakeupScheduleEntry())
            elif entry['type'] == 'idle':
                entries.append(IdleScheduleEntry())
            elif entry['type'] == 'shutdown':
                entries.append(ShutdownScheduleEntry())
            elif entry['type'] == 'opstatus':
                entries.append(GetOperationStatusScheduleEntry(network.get_node(entry['node'])))
            elif entry['type'] == 'pwrstatus':
                entries.append(GetPowerStatusScheduleEntry(network.get_node(entry['node'])))
            elif entry['type'] == 'serial':
                entries.append(GetSerialNumberScheduleEntry(network.get_node(entry['node'])))
            elif entry['type'] == 'swversion':
                entries.append(GetSoftwareVersionScheduleEntry(network.get_node(entry['node'])))
            elif entry['type'] == 'request':
                entries.append(RequestScheduleEntry(network.get_request(entry['request'])))
        schedule = Schedule(name, sche['delay'], entries)
        schedules.append(schedule)
    return schedules

def load_network(path: str) -> Network:
    with open(path, 'r') as f:
        data = json.load(f)

    network = Network(data['name'])
    network.baudrate = data['baudrate']

    for (name, enc) in data['encoders'].items():
        if enc['type'] == 'formula':
            network.encoders.append(FormulaEncoder(name, enc['scale'], enc['offset']))
        elif enc['type'] == 'mapping':
            mapping = dict([(int(k), v) for k, v in enc['mapping'].items()])
            network.encoders.append(MappingEncoder(name, mapping))
    
    for (name, req) in data['requests'].items():
        signals = []
        for (sig_name, sig) in req['layout'].items():
            try:
                encoder = network.get_encoder(sig['encoder'])
            except KeyError:
                encoder = NoneEncoder('none')

            signal = Signal(sig_name, to_int(sig['offset']), to_int(sig['width']), sig['initial'] if 'initial' in sig else 0, encoder)
            signals.append(signal)

        network.requests.append(Request(name, to_int(req['id']), to_int(req['size']), signals))

    for (name, nod) in data['nodes'].items():
        node = Node(name, to_int(nod['address']))
        node.publishes = [network.get_request(x) for x in nod['publishes']]
        node.subscribes = [network.get_request(x) for x in nod['subscribes']]
        network.nodes.append(node)

    schedules = load_schedules(network, data['schedules'])
    network.schedules += schedules

    return network
