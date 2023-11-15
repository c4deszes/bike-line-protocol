from dataclasses import dataclass
from typing import List, Union, Dict

class SignalEncoder:

    def __init__(self, name: str) -> None:
        self.name = name

    def encode(self, value: Union[str, int, float]) -> int:
        pass

    def decode(self, value: int) -> Union[str, int, float]:
        pass

class NoneEncoder(SignalEncoder):

    def __init__(self, name: str) -> None:
        super().__init__(name)

    def encode(self, value: int) -> int:
        return value
    
    def decode(self, value: int) -> int:
        return value

class FormulaEncoder(SignalEncoder):

    def __init__(self, name: str, scale: float, offset: float) -> None:
        super().__init__(name)
        self.scale = scale
        self.offset = offset

class MappingEncoder(SignalEncoder):

    def __init__(self, name: str, mapping: Dict[int, str]) -> None:
        super().__init__(name)
        self.mapping = mapping

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
        self.signals = signals

    def encode(self):
        raise NotImplementedError()
    
    def decode(self):
        raise NotImplementedError()
