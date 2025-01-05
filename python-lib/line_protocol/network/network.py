from typing import Union, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .nodes import Node
    from .request import Request, SignalEncoder
    from .schedule import Schedule

class Network:

    def __init__(self, name: str) -> None:
        self.name = name
        self.baudrate: int = 0
        self.nodes = []
        self.requests = []
        self.encoders = []
        self.schedules = []

    def get_node(self, name: str) -> 'Node':
        """
        Returns the node with the given name

        :param name: Node name
        :type name: str
        :raises LookupError: when no nodes match the name
        :return: Node
        :rtype: Node
        """
        for a in self.nodes:
            if a.name == name:
                return a
        raise LookupError(f'No such node: {name}')
    
    def get_nodes(self) -> List['Node']:
        return self.nodes

    def get_request(self, id: Union[int, str]) -> 'Request':
        """
        Returns the request with the given ID or name

        :param id: ID or Name
        :type id: Union[int, str]
        :raises LookupError: when no requests match the identifier
        :return: Request
        :rtype: Request
        """
        for a in self.requests:
            if a.name == id or a.id == id:
                return a
        raise LookupError(f'No such request: {id}')

    def get_encoder(self, name: str) -> 'SignalEncoder':
        """
        Returns the encoder with the given name

        :param name: Name of the encoder
        :type name: str
        :raises LookupError: when no encoder matches the name
        :return: SignalEncoder
        :rtype: SignalEncoder
        """
        for a in self.encoders:
            if a.name == name:
                return a
        raise LookupError(f'No such encoder: {name}')
    
    def get_schedule(self, name: str) -> 'Schedule':
        """
        Returns the schedule with the given name

        :param name: Name of the schedule
        :type name: str
        :raises LookupError: when no schedule matches the name
        :return: Schedule
        :rtype: Schedule
        """
        for a in self.schedules:
            if a.name == name:
                return a
        raise LookupError(f'No such schedule: {name}')
