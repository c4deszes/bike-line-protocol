import os
import sys
import argparse
from jinja2 import Environment, PackageLoader, select_autoescape

from ..network import Network, load_network, Node

def codegen(network: Network, node: Node, output_path: str):
    env = Environment(
        loader=PackageLoader('line_protocol', 'codegen'),
        autoescape=select_autoescape()
    )
    template = env.get_template('header.jinja2')
    output = template.render(network=network, node=node)
    os.makedirs(output_path, exist_ok=True)
    with open(os.path.join(output_path, 'line_api.h'), 'w+') as f:
        f.write(output)

    template = env.get_template('source.jinja2')
    output = template.render(network=network, node=node)
    os.makedirs(output_path, exist_ok=True)
    with open(os.path.join(output_path, 'line_api.c'), 'w+') as f:
        f.write(output)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('network')
    parser.add_argument('--node', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    network = load_network(args.network)

    codegen(network, network.get_node(args.node), args.output)

if __name__ == '__main__':
    sys.exit(main())
