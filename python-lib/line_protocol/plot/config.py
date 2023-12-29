from typing import List
import json
import os

from ..network import Network, Signal, Request
from ..network.schedule import Schedule
from ..network import load_network
from ..network.loader import load_schedules

class SignalRef:
    request: Request
    signal: Signal

class Plot:
    name: str
    signals: List[SignalRef]

class MonitoringConfig:
    network: Network
    customSchedules: List[Schedule]
    preStartSchedules: List[Schedule]
    mainSchedule: Schedule
    plots: List[Plot]

def load_config(path: str) -> MonitoringConfig:
    with open(path, 'r') as f:
        data = json.load(f)

    network = load_network(os.path.normpath(os.path.join(os.path.dirname(path), data['network'])))

    config = MonitoringConfig()
    config.network = network
    config.network.schedules += load_schedules(network, data['customSchedules'])

    config.preStartSchedules = [network.get_schedule(y) for y in data['prestartSchedules']]
    config.mainSchedule = network.get_schedule(data['mainSchedule'])

    return config
