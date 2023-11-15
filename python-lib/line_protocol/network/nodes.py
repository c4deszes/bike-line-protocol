from .request import Request

class Node:

    def __init__(self, name: str, address: int) -> None:
        self.name = name
        self.address = address
        self.publishes = []
        self.subscribes = []
