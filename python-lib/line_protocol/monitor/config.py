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

class PlotConfig:
    name: str
    signals: List[SignalRef]

class MonitoringConfig:
    network: Network
    customSchedules: List[Schedule]
    preStartSchedules: List[Schedule]
    mainSchedule: Schedule
    plots: List[PlotConfig]
    # TODO: duration attribute

def to_signal_ref(network: Network, ref: str) -> SignalRef:
    ref = ref.split('.')
    output = SignalRef()
    output.request = network.get_request(ref[0])
    output.signal = output.request.get_signal(ref[1])

    return output

def load_config(path: str) -> MonitoringConfig:
    with open(path, 'r') as f:
        data = json.load(f)

    network = load_network(os.path.normpath(os.path.join(os.path.dirname(path), data['network'])))

    config = MonitoringConfig()
    config.network = network
    config.network.schedules += load_schedules(network, data['customSchedules'])

    config.preStartSchedules = [network.get_schedule(y) for y in data['prestartSchedules']]
    config.mainSchedule = network.get_schedule(data['mainSchedule'])
    # TODO: load duration attribute

    config.plots = []
    for (name, settings) in data['plots'].items():
        plot = PlotConfig()
        plot.name = name
        plot.signals = []
        # TODO: do not allow empty plots
        for sig in settings['signals']:
            # TODO: do not allow plots with signals using different encoders
            ref = to_signal_ref(network, sig)
            plot.signals.append(to_signal_ref(network, sig))

    return config
