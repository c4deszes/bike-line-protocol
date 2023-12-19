from .nodes import Node
from .request import Request, SignalEncoder
from typing import Union, List

class Network:

    def __init__(self, name: str) -> None:
        self.name = name
        self.baudrate = 0
        self.nodes = []
        self.requests = []
        self.encoders = []

    def get_node(self, name: str) -> Node:
        for a in self.nodes:
            if a.name == name:
                return a
        raise LookupError('No such node.')

    def get_request(self, id: Union[int, str]) -> Request:
        for a in self.requests:
            if a.name == id or a.id == id:
                return a
        raise LookupError('No such request.')

    def get_encoder(self, name: str) -> SignalEncoder:
        for a in self.encoders:
            if a.name == name:
                return a
        raise LookupError('No such encoder.')
