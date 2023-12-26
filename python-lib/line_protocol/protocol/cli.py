from typing import Literal, List, Union
from .transport import LineSerialTransport
from .master import LineMaster
from .constants import *
from ..network import load_network
from types import SimpleNamespace
import logging
import argparse
import sys
import time

def main():
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('network')
    parser.add_argument('--port', required=True)
    args = parser.parse_args()

    network = load_network(args.network)

    with LineSerialTransport(args.port, baudrate=network.baudrate, one_wire=True) as transport:
        master = LineMaster(transport)

        for _ in range(100):
            data = master.transport.request_data(0x1000)
            request = network.get_request('SpeedStatus')
            print(request.decode(data))
            time.sleep(0.1)

if __name__ == '__main__':
    sys.exit(main())
