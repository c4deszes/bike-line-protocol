from typing import Literal, List, Union, TYPE_CHECKING
from types import SimpleNamespace
import logging
import argparse
import sys
import time

from ..protocol.transport import LineSerialTransport
from .traffic import TrafficLogger
from ..protocol.master import LineMaster
from ..protocol.constants import *
from ..network import load_network
from .config import MonitoringConfig, load_config

def main():
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('--port', required=True)
    parser.add_argument('--master', action='store_true', default=False)
    args = parser.parse_args()

    config = load_config(args.config)

    if args.master:
        with LineSerialTransport(args.port, baudrate=config.network.baudrate, one_wire=True) as transport:
            traffic_logger = TrafficLogger()
            transport.add_listener(traffic_logger)

            master = LineMaster(transport, config.network)

            try:
                for schedule in config.preStartSchedules:
                    schedule.perform(master)

                while True:
                    config.mainSchedule.perform(master)
            except KeyboardInterrupt:
                pass

            traffic_logger.dump_json('log.txt')
    else:
        # TODO: implement listener
        pass

if __name__ == '__main__':
    sys.exit(main())
