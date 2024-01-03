from .config import SignalRef
from typing import Dict, Any, List
from dataclasses import dataclass
import time

@dataclass(frozen=True)
class DataPoint:
    timestamp: float
    value: Any

@dataclass
class TimeSeries:
    data: List[DataPoint]

class SignalListener:

    def on_signal(self, timestamp: float, ref: SignalRef, value):
        raise NotImplementedError()

class Measurement(SignalListener):
    start: float
    data: Dict[SignalRef, TimeSeries]

    def __init__(self) -> None:
        self.start = time.time()
        self.data = {}

    def on_signal(self, timestamp: float, ref: SignalRef, value):
        if ref not in self.data:
            self.data[ref] = TimeSeries([])
        self.data[ref].data.append(DataPoint(timestamp-self.start, value))

    def dump_csv(self, path: str):
        with open(path, 'w+') as f:
            for key in self.data:
                f.write(';')
                f.write(str(key))
                f.write(';')
            f.write('\n')

            index = 0
            has_data = True

            while has_data:
                has_data = False
                for (signal_ref, series) in self.data.items():
                    if len(series.data) > index:
                        has_data = True
                        f.write(f"{series.data[index].timestamp};{series.data[index].value};")
                    else:
                        f.write(";;")
                index += 1
                f.write('\n')

