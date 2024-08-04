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

    def __init__(self, name: str, scale: float, offset: float) -> None:
        super().__init__(name)
        self.scale = scale
        self.offset = offset

    def encode(self, value: float) -> int:
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
        raise KeyError()
    
    def decode(self, value: int) -> str:
        return self.mapping[value]

@dataclass(unsafe_hash=True)
class Signal():
    name: str
    offset: int
    width: int
    initial: Union[int, float, str]
    encoder: SignalEncoder

class Request():

    def __init__(self, name: str, id: int, size: int, signals: List[Signal]) -> None:
        self.name = name
        self.id = id
        self.size = size
        self.signals = sorted(signals, key=lambda x: x.offset)
        _packed = Request.packer(self.signals, self.size)

        class RequestData(ctypes.LittleEndianStructure):
            nonlocal _packed
            _fields_ = _packed

            def __init__(self):
                super().__init__()

            def _to_dict(self):
                return {field[0]: getattr(self, field[0]) for field in self._fields_}

            @property
            def fields(self):
                return self._to_dict()

        self.data_class = RequestData

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
    
    def encode_raw(self, signals: Dict[str, int]):
        raise NotImplementedError()

    def encode(self, signals: Dict[str, Union[str, int, float]]):
        data = self.data_class()
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
            setattr(data, signal.name, value)
        return list(bytes(data))
    
    def decode_raw(self, data) -> Dict[str, int]:
        # TODO: in some requests the length required is longer than the actual length
        decoded = self.data_class.from_buffer_copy(bytes(data + [0]))
        return decoded.fields

    def decode(self, data: Iterable[int]) -> Dict[str, Union[int, str, float]]:
        values = self.decode_raw(data)
        for key in values.keys():
            values[key] = self.get_signal(key).encoder.decode(values[key])
        return values
