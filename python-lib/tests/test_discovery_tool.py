import sys
from unittest.mock import patch
import pytest

from line_protocol.util.discovery import main

class TestLineDiscoveryCli:

    @pytest.mark.xfail(reason="This test is expected to fail due to port number")
    @pytest.mark.unit
    @pytest.mark.parametrize('command', [
        ['line-discovery', '--port', 'COM20'],
        ['line-discovery', '--port', 'COM20', '--baudrate', '19200'],
    ])
    def test_Discovery_WithoutNetwork(self, command):
        with pytest.raises(SystemExit) as exit_ex, patch.object(sys, 'argv', command):
            main()
        assert exit_ex.value.code == 0

    @pytest.mark.xfail(reason="This test is expected to fail due to port number")
    @pytest.mark.unit
    @pytest.mark.parametrize('command', [
        ['line-discovery', '--port', 'COM20', '--network', 'data/network-1.json'],
        ['line-discovery', '--port', 'COM20', '--network', 'data/network-1.json', '--baudrate', '19200'],
    ])
    def test_Discovery_WithNetwork(self, command):
        with pytest.raises(SystemExit) as exit_ex, patch.object(sys, 'argv', command):
            main()
        assert exit_ex.value.code == 0
