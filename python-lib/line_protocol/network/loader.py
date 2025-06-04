from .network import Network
from .request import FormulaEncoder, MappingEncoder, Request, Signal, NoneEncoder
from .nodes import Node
from typing import List
from .schedule import Schedule, FixedOrderSchedule, PriorityScheduleEntry, PriorityAgingSchedule, RequestScheduleEntry, WakeupScheduleEntry, IdleScheduleEntry, ShutdownScheduleEntry, GetOperationStatusScheduleEntry, GetPowerStatusScheduleEntry, GetSerialNumberScheduleEntry, GetSoftwareVersionScheduleEntry

import json

def to_int(value: str) -> int:
    if isinstance(value, int):
        return value
    return int(value, base=0)

def load_schedules(network, obj: dict) -> List[Schedule]:
    schedules = []
    for (name, sche) in obj.items():
        if 'type' not in sche or sche['type'] == 'fixed':
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
            schedule = FixedOrderSchedule(name, entries, sche['slots'] if 'slots' in sche else 'variable', reserve_slots=True, delay=sche['delay'])
        elif sche['type'] == 'priority-aging':
            entries = []
            for entry in sche['entries']:
                if entry['type'] == 'wakeup':
                    entries.append(PriorityScheduleEntry(WakeupScheduleEntry(), entry['cycle'], entry['maxAge']))
                elif entry['type'] == 'idle':
                    entries.append(PriorityScheduleEntry(IdleScheduleEntry(), entry['cycle'], entry['maxAge']))
                elif entry['type'] == 'shutdown':
                    entries.append(PriorityScheduleEntry(ShutdownScheduleEntry(), entry['cycle'], entry['maxAge']))
                elif entry['type'] == 'opstatus':
                    entries.append(PriorityScheduleEntry(GetOperationStatusScheduleEntry(network.get_node(entry['node'])), entry['cycle'], entry['maxAge']))
                elif entry['type'] == 'pwrstatus':
                    entries.append(PriorityScheduleEntry(GetPowerStatusScheduleEntry(network.get_node(entry['node'])), entry['cycle'], entry['maxAge']))
                elif entry['type'] == 'serial':
                    entries.append(PriorityScheduleEntry(GetSerialNumberScheduleEntry(network.get_node(entry['node'])), entry['cycle'], entry['maxAge']))
                elif entry['type'] == 'swversion':
                    entries.append(PriorityScheduleEntry(GetSoftwareVersionScheduleEntry(network.get_node(entry['node'])), entry['cycle'], entry['maxAge']))
                elif entry['type'] == 'request':
                    entries.append(PriorityScheduleEntry(RequestScheduleEntry(network.get_request(entry['request'])), entry['cycle'], entry['maxAge']))
            schedule = PriorityAgingSchedule(name, entries, sche['slots'], sche['phase'], reserve_slots=True, delay=sche['delay'])
        else:
            raise ValueError(f"Unknown schedule type: {sche['type']}")
        schedules.append(schedule)
    return schedules

def load_network(path: str) -> Network:
    with open(path, 'r') as f:
        data = json.load(f)

    network = Network()
    network.baudrate = data['baudrate']

    for (name, enc) in data['encoders'].items():
        if enc['type'] == 'formula':
            network.encoders.append(FormulaEncoder(name, enc['scale'], enc['offset'], enc['unit'] if 'unit' in enc else ''))
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

    network.master = network.get_node(data['master'])

    schedules = load_schedules(network, data['schedules'])
    network.schedules += schedules

    return network
