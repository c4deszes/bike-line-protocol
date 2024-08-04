from .request import Request
from typing import List

class Node:

    def __init__(self, name: str, address: int) -> None:
        self.name = name
        self.address = address
        self.publishes: List[Request] = []
        self.subscribes: List[Request] = []
