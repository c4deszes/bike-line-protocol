from typing import Union, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .nodes import Node
    from .request import Request, SignalEncoder
    from .schedule import Schedule

class Network:

    def __init__(self, name: str) -> None:
        self.name = name
        self.baudrate = 0
        self.nodes = []
        self.requests = []
        self.encoders = []
        self.schedules = []

    def get_node(self, name: str) -> 'Node':
        for a in self.nodes:
            if a.name == name:
                return a
        raise LookupError('No such node.')

    def get_request(self, id: Union[int, str]) -> 'Request':
        for a in self.requests:
            if a.name == id or a.id == id:
                return a
        raise LookupError('No such request.')

    def get_encoder(self, name: str) -> 'SignalEncoder':
        for a in self.encoders:
            if a.name == name:
                return a
        raise LookupError('No such encoder.')
    
    def get_schedule(self, name: str) -> 'Schedule':
        for a in self.schedules:
            if a.name == name:
                return a
        raise LookupError('No such schedule.')
