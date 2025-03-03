import os
import sys
from unittest.mock import patch
import pytest

from line_protocol.network import load_network
from line_protocol.codegen import codegen
from line_protocol.codegen.generator import main

# class TestCodeGeneration():

#     def test_GenerateCode_1(self, tmp_path):
#         path = os.path.join(os.path.dirname(__file__), 'data', 'network-1.json')
#         network = load_network(path)

#         codegen(network, network.get_node('RotorSensor'), tmp_path)

#         # TODO: assert that generated files exist
#         # TODO: check that they compile fine

class TestCodeGenerationCommand():

    def test_CodegenCall_1(self, tmp_path):
        path = os.path.join(os.path.dirname(__file__), 'data', 'codegen.json')
        command = ['line-codegen', path, '--output', str(tmp_path)]

        with patch.object(sys, 'argv', command):
            assert main() == 0

        # TODO: assert that generated files exist
