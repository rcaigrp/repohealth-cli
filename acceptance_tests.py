import pytest
import json
import main

class TestLocalTracker:
    def test_calculate_duration(self):
        result = main.calculate_duration('2024-01-01 09:00', '2024-01-01 10:00')
        assert result == 1.0

    def test_parse_entries(self):
        data = json.dumps([{'project': 'A', 'hours': 2}])
        result = main.parse_entries(data)
        assert isinstance(result, list)

    def test_format_duration(self):
        assert main.format_duration(1.5) == '1.50'
        assert main.format_duration(-1) == '0.00'