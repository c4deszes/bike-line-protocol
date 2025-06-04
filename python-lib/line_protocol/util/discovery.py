from typing import Literal, List, Union, TYPE_CHECKING, Dict
from types import SimpleNamespace
import logging
import argparse
import sys
import time

from ..protocol.transport import LineSerialTransport, LineTransportTimeout
from ..protocol.master import LineMaster, NodeStatus
from ..protocol.constants import *
from ..network import Network, load_network, Node

def network_discovery(master: LineMaster, start: int = 1, end: int = 14,
                      network: Network = None) -> Dict[Union[int, str], NodeStatus]:
    
    nodes = {}

    for address in range(1, LINE_DIAG_UNICAST_BROADCAST_ID):
        if network is not None:
            try:
                key = network.get_node_by_address(address)
            except LookupError:
                key = address
        else:
            key = address

        try:
            node_status = NodeStatus(None, None, None, None)
            node_status.op_status = master.get_operation_status(address)

            # TODO: implement
            # disabled as power status is not consistent across all devices
            # try:
            #     pwr_status = master.get_power_status(address)
            #     node.append(pwr_status)
            # except LineTransportTimeout:
            #     node.append('N/A')

            try:
                node_status.software_version = master.get_software_version(address)
            except LineTransportTimeout:
                pass

            try:
                node_status.serial_number = master.get_serial_number(address)
            except LineTransportTimeout:
                pass

            nodes[key] = node_status
        except LineTransportTimeout:
            pass

    return nodes

def main():
    logging.basicConfig(level=logging.CRITICAL)

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=True)
    parser.add_argument('--baudrate', default=19200, type=int)
    parser.add_argument('--network', default=None, type=str)
    args = parser.parse_args()

    if args.network is not None:
        network = load_network(args.network)
    else:
        network = None

    with LineSerialTransport(args.port,
                             baudrate=args.baudrate if network is None else network.baudrate,
                             one_wire=True) as transport:
        with LineMaster(transport) as master:

            master.wakeup()

            time.sleep(0.5)

            nodes = network_discovery(master, network=network)

            for (node, status) in nodes.items():
                if isinstance(node, Node):
                    peripheral = f"{node.name}(0x{node.address:01X})"
                else:
                    peripheral = f"0x{node:01X}"

                if status.op_status is not None:
                    op_status = status.op_status
                else:
                    op_status = 'N/A'

                if status.software_version is not None:
                    sw_version = status.software_version
                else:
                    sw_version = 'N/A'

                if status.serial_number is not None:
                    serial_number = f"{status.serial_number:08X}"
                else:
                    serial_number = 'N/A'

                print(f"Peripheral {peripheral} - STATUS: {op_status} - SW: {sw_version} - SERIAL: {serial_number}")

            if len(nodes) == 0:
                print("No peripherals found.")

if __name__ == '__main__':
    sys.exit(main())
