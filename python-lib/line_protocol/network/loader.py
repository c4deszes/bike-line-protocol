from .network import Network
from .request import FormulaEncoder, MappingEncoder, Request, Signal, NoneEncoder, SignalEncoder
from .nodes import Node
from typing import List
from .schedule import ScheduleEntry, Schedule, FixedOrderSchedule, PriorityScheduleEntry, PriorityAgingSchedule, RequestScheduleEntry, WakeupScheduleEntry, IdleScheduleEntry, ShutdownScheduleEntry, GetOperationStatusScheduleEntry, GetPowerStatusScheduleEntry, GetSerialNumberScheduleEntry, GetSoftwareVersionScheduleEntry

import json

def to_int(value: str) -> int:
    if isinstance(value, int):
        return value
    return int(value, base=0)

def parse_schedule_entry(name: str, entry: dict, network) -> ScheduleEntry:
    if 'type' not in entry:
        raise ValueError(f"{name}: Schedule entry must have 'type' defined")

    if entry['type'] == 'wakeup':
        return WakeupScheduleEntry()
    elif entry['type'] == 'idle':
        return IdleScheduleEntry()
    elif entry['type'] == 'shutdown':
        return ShutdownScheduleEntry()
    elif entry['type'] == 'opstatus':
        if 'node' not in entry:
            raise ValueError(f"{name}: 'opstatus' entry must have 'node' defined")
        return GetOperationStatusScheduleEntry(network.get_node(entry['node']))
    elif entry['type'] == 'pwrstatus':
        if 'node' not in entry:
            raise ValueError(f"{name}: 'pwrstatus' entry must have 'node' defined")
        return GetPowerStatusScheduleEntry(network.get_node(entry['node']))
    elif entry['type'] == 'serial':
        if 'node' not in entry:
            raise ValueError(f"{name}: 'serial' entry must have 'node' defined")
        return GetSerialNumberScheduleEntry(network.get_node(entry['node']))
    elif entry['type'] == 'swversion':
        if 'node' not in entry:
            raise ValueError(f"{name}: 'swversion' entry must have 'node' defined")
        return GetSoftwareVersionScheduleEntry(network.get_node(entry['node']))
    elif entry['type'] == 'request':
        if 'request' not in entry:
            raise ValueError(f"{name}: 'request' entry must have 'request' defined")
        return RequestScheduleEntry(network.get_request(entry['request']))
    else:
        raise ValueError(f"{name}: Unknown schedule entry type: {entry['type']}")

def parse_fixed_order_schedule(name: str, schedule: dict, network) -> FixedOrderSchedule:
    entries = []
    for entry in schedule['entries']:
        entries.append(parse_schedule_entry(name, entry, network))
    return FixedOrderSchedule(name, entries, schedule['slots'] if 'slots' in schedule else 'variable', reserve_slots=True, delay=schedule['delay'])

def parse_priority_aging_schedule(name: str, schedule: dict, network) -> PriorityAgingSchedule:
    entries = []
    for entry in schedule['entries']:
        if 'cycle' not in entry or 'maxAge' not in entry:
            raise ValueError(f"{name}: Priority aging entry must have 'cycle' and 'maxAge' defined")
        entries.append(PriorityScheduleEntry(parse_schedule_entry(name, entry, network), entry['cycle'], entry['maxAge']))
    return PriorityAgingSchedule(name, entries, schedule['slots'] if 'slots' in schedule else 'variable', schedule['phase'], reserve_slots=True, delay=schedule['delay'])

def load_schedules(network, obj: dict) -> List[Schedule]:
    schedules = []
    for (name, sche) in obj.items():
        if 'type' not in sche or sche['type'] == 'fixed':
            schedule = parse_fixed_order_schedule(name, sche, network)
        elif sche['type'] == 'priority-aging':
            schedule = parse_priority_aging_schedule(name, sche, network)
        else:
            raise ValueError(f"Unknown schedule type: {sche['type']}")
        schedules.append(schedule)
    return schedules

def parse_formula_encoder(name: str, encoder: dict) -> FormulaEncoder:
    if 'scale' not in encoder or 'offset' not in encoder:
        raise ValueError(f"{name}: Formula encoder must have 'scale' and 'offset' defined")
    return FormulaEncoder(name, encoder['scale'], encoder['offset'], encoder.get('unit', ''))

def parse_mapping_encoder(name: str, encoder: dict) -> MappingEncoder:
    if 'mapping' not in encoder:
        raise ValueError(f"{name}: Mapping encoder must have 'mapping' defined")
    mapping = {int(k): v for k, v in encoder['mapping'].items()}
    return MappingEncoder(name, mapping)

def parse_encoder(name: str, encoder: dict) -> SignalEncoder:
    if 'type' not in encoder:
        raise ValueError(f"{name}: Encoder must have 'type' defined")
    if encoder['type'] == 'formula':
        return parse_formula_encoder(name, encoder)
    elif encoder['type'] == 'mapping':
        return parse_mapping_encoder(name, encoder)
    else:
        raise ValueError(f"{name}: Unknown encoder type: {encoder['type']}")
    
def parse_signal(name: str, signal: dict, encoder: SignalEncoder) -> Signal:
    if 'offset' not in signal or 'width' not in signal:
        raise ValueError(f"Signal must have 'offset' and 'width' defined")
    offset = to_int(signal['offset'])
    width = to_int(signal['width'])
    initial = signal.get('initial', 0)
    return Signal(name, offset, width, initial, encoder)

def load_network(path: str) -> Network:
    with open(path, 'r') as f:
        data = json.load(f)

    network = Network()
    network.baudrate = data['baudrate']

    for (name, enc) in data['encoders'].items():
        network.encoders.append(parse_encoder(name, enc))

    for (name, req) in data['requests'].items():
        signals = []
        for (sig_name, sig) in req['layout'].items():
            if 'encoder' not in sig:
                encoder = NoneEncoder('none')
            else:
                encoder = network.get_encoder(sig['encoder'])

            signal = parse_signal(sig_name, sig, encoder)
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
