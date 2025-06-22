import pytest
import os

from line_protocol.util.schedule_analyze import analyze_schedule
from line_protocol.network import load_network

class TestScheduleAnalysis:

    @pytest.fixture
    def network(self):
        return load_network(os.path.join(os.path.dirname(__file__), 'data/schedules-test.json'))

    def test_ScheduleAnalysis_ByName(self, network):
        analyze_schedule('LegacySchedule', 10, network)
        # TODO: Add assertions to verify the analysis results

    def test_ScheduleAnalysis_ByObject(self, network):
        schedule = network.get_schedule('LegacySchedule')
        analyze_schedule(schedule, 10)
        # TODO: Add assertions to verify the analysis results
