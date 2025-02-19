from .request import Request
from typing import List, Union

class Node:

    def __init__(self, name: str, address: int) -> None:
        self.name = name
        self.address = address
        self.publishes: List[Request] = []
        self.subscribes: List[Request] = []

    def is_publishing(self, request: Union[int, str]) -> bool:
        return any([a.id == request or a.name == request for a in self.publishes])
