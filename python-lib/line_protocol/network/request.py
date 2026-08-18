from dataclasses import dataclass
from typing import List, Union, Dict, Iterable
import ctypes

class SignalEncoder:
    """
    SignalEncoder is an interface for classes that can convert in between the network representation
    of signal and their physical or system interpretation.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def encode(self, value: Union[str, int, float]) -> int:
        """
        Encoder takes strings or numbers and returns an integer that can be packed into responses

        :param value: Physical value
        :type value: Union[str, int, float]
        :return: Raw value
        :rtype: int
        """
        raise NotImplementedError()

    def decode(self, value: int) -> Union[str, int, float]:
        """
        Decoder takes raw network data and converts it into their physical representation

        :param value: Raw value
        :type value: int
        :return: Physical value
        :rtype: Union[str, int, float]
        """
        raise NotImplementedError()

class NoneEncoder(SignalEncoder):
    """
    NoneEncoder does no conversion when encoding or decoding, inputs are restricted to integers.
    """

    def __init__(self, name: str) -> None:
        super().__init__(name)

    def encode(self, value: int) -> int:
        if not isinstance(value, int):
            raise ValueError(f"Unable to encode non-integer {value}")
        return value

    def decode(self, value: int) -> int:
        return value

class FormulaEncoder(SignalEncoder):
    """
    Formula encoder takes a physical value and maps it to an integer range
    """

    def __init__(self, name: str, scale: float, offset: float, unit: str) -> None:
        super().__init__(name)
        self.scale = scale
        self.offset = offset
        self.unit = unit

    def encode(self, value: float) -> int:
        if isinstance(value, str):
            value = float(value)
        return int((value - self.offset) / self.scale)

    def decode(self, value: int) -> float:
        return value * self.scale + self.offset

class MappingEncoder(SignalEncoder):
    """
    Mapping encoder takes labels and maps them to integer values
    """

    def __init__(self, name: str, mapping: Dict[int, str]) -> None:
        super().__init__(name)
        self.mapping = mapping

    def encode(self, value: str) -> int:
        for (key, val) in self.mapping.items():
            if val == value:
                return key
        raise ValueError(f'{self.name}: Unable to encode {value}')

    def decode(self, value: int) -> str:
        if value in self.mapping:
            return self.mapping[value]
        raise ValueError(f'{self.name}: Value {value} is not mapped')

class TwosComplementEncoder(SignalEncoder):
    """
    TwosComplementEncoder is a special encoder for signed integers
    """

    def __init__(self, name: str, width: int) -> None:
        super().__init__(name)
        self.width = width

    def encode(self, value: int) -> int:
        if value < 0:
            return (1 << self.width) + value
        return value
    
    def decode(self, value: int) -> int:
        if value & (1 << (self.width - 1)):
            return value - (1 << self.width)
        return value

@dataclass(unsafe_hash=True)
class Signal():
    name: str
    offset: int
    width: int
    initial: Union[int, float, str]
    encoder: SignalEncoder

@dataclass(unsafe_hash=True)
class SignalValue:
    signal: Signal
    phy: Union[int, float, str]
    raw: int

class SignalValueContainer():

    def __init__(self, signals: List[SignalValue]) -> None:
        self._signals = {signal.signal.name: signal for signal in signals}

    def get_signal(self, name: str) -> SignalValue:
        if name in self._signals:
            return self._signals[name]
        raise KeyError(f'Signal {name} not found')

    def __getitem__(self, name: str) -> SignalValue:
        return self.get_signal(name)

    def __contains__(self, name: str) -> bool:
        return name in self._signals

    def __iter__(self):
        return iter(self._signals.values())

class Request():

    def __init__(self, name: str, id: int, size: int, signals: List[Signal]) -> None:
        self.name = name
        self.id = id
        self.size = size
        self.signals = sorted(signals, key=lambda x: x.offset)
        for signal in self.signals:
            if signal.offset < 0 or signal.width <= 0 or signal.offset + signal.width > size * 8:
                raise ValueError(f'{signal.name} spans outside the frame!')
        self.data_class = ctypes.c_uint8 * size

    def __len__(self):
        return self.size + 1 + 2 + 1 + 1 # sync, id, size, crc

    @staticmethod
    def packer(signals, size):
        fields = []
        paddings = 0
        offset = 0
        for signal in signals:
            if offset + signal.width > size * 8:
                raise ValueError(f'{signal.name} spans outside the frame!')
            if signal.offset != offset:
                padding = signal.offset - offset
                # TODO: type should depend on width
                fields.append((f'Padding{paddings}', ctypes.c_uint16, padding))
                paddings += 1
                offset += padding
            if signal.width <= 8:
                fields.append((signal.name, ctypes.c_uint8, signal.width))
            elif signal.width <= 16:
                fields.append((signal.name, ctypes.c_uint16, signal.width))
            elif signal.width <= 32:
                fields.append((signal.name, ctypes.c_uint32, signal.width))
            offset += signal.width
        return fields

    def get_signal(self, name: str) -> Signal:
        for x in self.signals:
            if x.name == name:
                return x
        raise KeyError()

    def encode_raw(self, signals: Dict[str, int]) -> List[int]:
        raise NotImplementedError()

    def encode(self, signals: Dict[str, Union[str, int, float]]) -> List[int]:
        data = 0
        for signal in self.signals:
            if signal.name in signals:
                if signal.encoder != None:
                    value = signal.encoder.encode(signals[signal.name])
                else:
                    value = signals[signal.name]
            else:
                if signal.encoder != None:
                    value = signal.encoder.encode(signal.initial)
                else:
                    value = signal.initial
            data |= (value & ((1 << signal.width) - 1)) << signal.offset
        return list(data.to_bytes(self.size, byteorder='little'))

    def decode_raw(self, data) -> Dict[str, int]:
        payload = bytes(data)
        if len(payload) != self.size:
            raise ValueError(f'{self.name}: Expected {self.size} bytes, got {len(payload)}')
        raw_data = int.from_bytes(payload, byteorder='little')
        return {
            signal.name: (raw_data >> signal.offset) & ((1 << signal.width) - 1)
            for signal in self.signals
        }

    def decode(self, data: Iterable[int]) -> SignalValueContainer:
        decoded = self.decode_raw(data)
        signals = []
        for signal in self.signals:
            if signal.name in decoded:
                raw_value = decoded[signal.name]
                phy_value = signal.encoder.decode(raw_value) if signal.encoder else raw_value
                signals.append(SignalValue(signal, phy_value, raw_value))
            else:
                raise KeyError(f'Signal {signal.name} not found in decoded data')
        return SignalValueContainer(signals)

@dataclass
class SignalRef:
    request: Request
    signal: Signal

    def __hash__(self):
        return hash((self.request.name, self.signal.name))
