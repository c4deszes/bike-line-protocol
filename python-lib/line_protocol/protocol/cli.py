from typing import Literal, List, Union, TYPE_CHECKING
from types import SimpleNamespace
import logging
import argparse
import sys
import time

from .transport import LineSerialTransport
from .master import LineMaster
from .constants import *
from ..network import load_network
from ..plot.config import MonitoringConfig, load_config

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
            master = LineMaster(transport, config.network)

            for schedule in config.preStartSchedules:
                schedule.perform(master)

            while True:
                config.mainSchedule.perform(master)
    else:
        # TODO: implement listener
        pass

if __name__ == '__main__':
    sys.exit(main())
