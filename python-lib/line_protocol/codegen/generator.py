import os
import sys
import argparse
from dataclasses import dataclass
from jinja2 import Environment, PackageLoader, select_autoescape

from ..network import Network, load_network, Node
import json

@dataclass
class Channel:
    name: str
    channel: int
    one_wire: bool
    network: Network
    nodes: list[Node]

@dataclass
class NodeSettings:
    node: Node
    enabled: bool

def codegen(channels: list[Node], output_path: str):
    env = Environment(
        loader=PackageLoader('line_protocol', 'codegen'),
        autoescape=select_autoescape()
    )
    template = env.get_template('header.jinja2')
    output = template.render(channels=channels)
    os.makedirs(output_path, exist_ok=True)
    with open(os.path.join(output_path, 'line_api.h'), 'w+') as f:
        f.write(output)

    template = env.get_template('source.jinja2')
    output = template.render(channels=channels)
    os.makedirs(output_path, exist_ok=True)
    with open(os.path.join(output_path, 'line_api.c'), 'w+') as f:
        f.write(output)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('--output', default='.')
    args = parser.parse_args()

    with open(args.config, 'r') as f:
        config_data = json.load(f)
        channels = []

        for (name, props) in config_data.items():
            network = load_network(props['network'])
            nodes = []

            for node_name, node_props in props['nodes'].items():
                nodes.append(NodeSettings(
                    node=network.get_node(node_name),
                    enabled=bool(node_props['enabled'])
                ))

            channel = Channel(
                name=name,
                channel=int(props['channel']),
                one_wire=bool(props['oneWire']),
                network=network,
                nodes=nodes
            )
            channels.append(channel)

    codegen(channels, args.output)

    return 0

if __name__ == '__main__':
    sys.exit(main())
