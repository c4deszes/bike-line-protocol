from dataclasses import dataclass
from typing import List, Union, Dict, Iterable
import bitstruct
import bitstring

class SignalEncoder:

    def __init__(self, name: str) -> None:
        self.name = name

    def encode(self, value: Union[str, int, float]) -> int:
        raise NotImplementedError()

    def decode(self, value: int) -> Union[str, int, float]:
        raise NotImplementedError()

class NoneEncoder(SignalEncoder):

    def __init__(self, name: str) -> None:
        super().__init__(name)

    def encode(self, value: int) -> int:
        return value
    
    def decode(self, value: int) -> int:
        return value

class FormulaEncoder(SignalEncoder):

    def __init__(self, name: str, scale: float, offset: float, unit: str) -> None:
        super().__init__(name)
        self.scale = scale
        self.offset = offset
        self.unit = unit

    def encode(self, value: float) -> int:
        return int((value - self.offset) / self.scale)
    
    def decode(self, value: int) -> float:
        return value * self.scale + self.offset

class MappingEncoder(SignalEncoder):

    def __init__(self, name: str, mapping: Dict[int, str]) -> None:
        super().__init__(name)
        self.mapping = mapping

    def encode(self, value: str) -> int:
        for (key, val) in self.mapping:
            if val == value:
                return key
        raise KeyError()
    
    def decode(self, value: int) -> str:
        return self.mapping[value]

@dataclass
class Signal():
    name: str
    offset: int
    width: int
    encoder: SignalEncoder

class Request():

    def __init__(self, name: str, id: int, size: int, signals: List[Signal]) -> None:
        self.name = name
        self.id = id
        self.size = size
        self.signals = sorted(signals, key=lambda x: x.offset)
        self.pattern_text = Request.packer(self.signals, self.size)
        print(self.pattern_text)

    @staticmethod
    def packer(signals, size):
        pattern = ''
        offset = 0
        for signal in signals:
            if offset + signal.width > size * 8:
                raise ValueError(f'{signal.name} spans outside the frame!')
            if signal.offset != offset:
                padding = signal.offset - offset
                pattern += f"p{padding}"
                offset+=padding
            pattern += f"uint"
            if signal.width % 8 == 0:
                pattern += 'le'
            pattern += f'{signal.width}'
            offset+=signal.width
            pattern += ','
        return pattern
    
    def get_signal(self, name: str) -> Signal:
        for x in self.signals:
            if x.name == name:
                return x
        raise KeyError()

    def encode(self, signals: Dict[str, Union[str, int, float]]):
        raise NotImplementedError()
    
    def decode_raw(self, data) -> Dict[str, int]:
        values = bitstring.BitArray(bytes(data)).unpack(self.pattern_text)
        return dict(zip([x.name for x in self.signals], values))

    def decode(self, data: Iterable[int]) -> Dict[str, Union[int, str, float]]:
        values = self.decode_raw(data)
        print(values)
        for key in values.keys():
            values[key] = self.get_signal(key).encoder.decode(values[key])
        return values
