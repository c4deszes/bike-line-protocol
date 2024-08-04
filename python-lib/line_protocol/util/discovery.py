from typing import Literal, List, Union, TYPE_CHECKING
from types import SimpleNamespace
import logging
import argparse
import sys
import time

from line_protocol.protocol.transport import LineSerialTransport, LineTransportTimeout
from line_protocol.protocol.master import LineMaster
from line_protocol.protocol.constants import *

def main():
    logging.basicConfig(level=logging.CRITICAL)

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=True)
    parser.add_argument('--baudrate', default=19200, type=int)
    args = parser.parse_args()

    with LineSerialTransport(args.port, baudrate=args.baudrate, one_wire=True) as transport:
        master = LineMaster(transport)

        master.wakeup()

        nodes = []

        for address in range(1, 14):
            try:
                node = [address]
                status = master.get_operation_status(address)
                node.append(status)

                # try:
                #     pwr_status = master.get_power_status(address)
                #     node.append(pwr_status)
                # except LineTransportTimeout:
                #     node.append('N/A')

                try:
                    sw_version = master.get_software_version(address)
                    node.append(sw_version)
                except LineTransportTimeout:
                    node.append('N/A')

                try:
                    serial_number = master.get_serial_number(address)
                    node.append(serial_number)
                except LineTransportTimeout:
                    node.append('N/A')

                nodes.append(node)
            except LineTransportTimeout:
                pass

        for node in nodes:
            print(f"Peripheral 0x{node[0]:01X} - STATUS: {node[1]} - SW: {node[2]} - SERIAL: {node[3]:08X}")

        if len(nodes) == 0:
            print("No peripherals found.")

if __name__ == '__main__':
    sys.exit(main())
