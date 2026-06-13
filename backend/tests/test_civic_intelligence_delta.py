import pytest
import json
import os
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime, timezone

from backend.models import Issue
from backend.civic_intelligence import CivicIntelligenceEngine

@pytest.fixture
def engine():
    return CivicIntelligenceEngine()

@patch('backend.civic_intelligence.SessionLocal')
@patch('backend.civic_intelligence.trend_analyzer')
@patch('backend.civic_intelligence.adaptive_weights')
@patch('builtins.open', new_callable=mock_open)
@patch('json.dump')
@patch('os.listdir')
def test_emerging_concern_growth_logic(mock_listdir, mock_json_dump, mock_file_open, mock_weights, mock_trend_analyzer, mock_db_session, engine):
    """
    Test that the top emerging concern is correctly identified based on the highest
    percentage growth compared to the previous day.
    """
    mock_session = MagicMock()
    mock_db_session.return_value = mock_session

    # Previous day snapshot with 'Water' at 4 and 'Fire' at 2
    mock_listdir.return_value = ['2023-01-01.json']
    previous_snapshot_content = json.dumps({
        "civic_index": {"score": 75.0},
        "trends": {
            "category_distribution": {"Fire": 2, "Water": 4}
        }
    })

    read_mock = mock_open(read_data=previous_snapshot_content)
    write_mock = mock_open()
    def open_side_effect(file, mode='r', *args, **kwargs):
        if 'r' in mode:
            return read_mock(file, mode, *args, **kwargs)
        return write_mock(file, mode, *args, **kwargs)
    mock_file_open.side_effect = open_side_effect

    mock_query_issues = MagicMock()
    mock_query_upgrades = MagicMock()
    mock_query_grievances = MagicMock()

    def query_side_effect(model):
        from backend.models import Issue, EscalationAudit, Grievance
        if model == Issue:
            return mock_query_issues
        elif model == EscalationAudit:
            return mock_query_upgrades
        elif model == Grievance:
            return mock_query_grievances
        return MagicMock()

    mock_session.query.side_effect = query_side_effect

    mock_query_issues.filter.return_value.all.return_value = []
    mock_query_issues.filter.return_value.count.return_value = 0
    mock_query_upgrades.filter.return_value.all.return_value = []
    mock_query_grievances.filter.return_value.all.return_value = []

    # Current day: 'Water' goes to 8 (100% growth), 'Fire' goes to 6 (200% growth)
    # Even though Water has more total volume, Fire should be the top emerging concern.
    mock_trend_analyzer.analyze.return_value = {
        "top_keywords": [],
        "category_distribution": {"Fire": 6, "Water": 8},
        "clusters": []
    }
    mock_weights.get_duplicate_search_radius.return_value = 50.0

    engine.run_daily_cycle()

    args, _ = mock_json_dump.call_args
    snapshot = args[0]

    assert "Fire" in snapshot["trends"]["spikes"]
    assert "Water" in snapshot["trends"]["spikes"]
    assert snapshot["trends"]["top_emerging_concern"] == "Fire"

@patch('backend.civic_intelligence.SessionLocal')
@patch('backend.civic_intelligence.trend_analyzer')
@patch('backend.civic_intelligence.adaptive_weights')
@patch('builtins.open', new_callable=mock_open)
@patch('json.dump')
@patch('os.listdir')
def test_civic_intelligence_index_delta(mock_listdir, mock_json_dump, mock_file_open, mock_weights, mock_trend_analyzer, mock_db_session, engine):
    """
    Test that the Civic Intelligence Index correctly calculates the delta from the previous day.
    """
    mock_session = MagicMock()
    mock_db_session.return_value = mock_session

    mock_listdir.return_value = ['2023-01-01.json']
    # Previous score is 72.0
    previous_snapshot_content = json.dumps({
        "civic_index": {"score": 72.0},
        "trends": {
            "category_distribution": {"Fire": 2}
        }
    })

    read_mock = mock_open(read_data=previous_snapshot_content)
    write_mock = mock_open()
    def open_side_effect(file, mode='r', *args, **kwargs):
        if 'r' in mode:
            return read_mock(file, mode, *args, **kwargs)
        return write_mock(file, mode, *args, **kwargs)
    mock_file_open.side_effect = open_side_effect

    mock_query_issues = MagicMock()
    mock_query_upgrades = MagicMock()
    mock_query_grievances = MagicMock()

    def query_side_effect(model):
        from backend.models import Issue, EscalationAudit, Grievance
        if model == Issue:
            return mock_query_issues
        elif model == EscalationAudit:
            return mock_query_upgrades
        elif model == Grievance:
            return mock_query_grievances
        return MagicMock()

    mock_session.query.side_effect = query_side_effect

    # 4 new issues (-2 penalty) and 3 resolved issues (+6 bonus)
    # Base 70 - 2 + 6 = 74.0
    issues_result = [Issue(id=1), Issue(id=2), Issue(id=3), Issue(id=4)]
    mock_query_issues.filter.return_value.all.return_value = issues_result
    mock_query_issues.filter.return_value.count.return_value = 3

    mock_query_upgrades.filter.return_value.all.return_value = []
    mock_query_grievances.filter.return_value.all.return_value = []

    mock_trend_analyzer.analyze.return_value = {
        "top_keywords": [],
        "category_distribution": {"Fire": 4},
        "clusters": []
    }
    mock_weights.get_duplicate_search_radius.return_value = 50.0

    engine.run_daily_cycle()

    args, _ = mock_json_dump.call_args
    snapshot = args[0]

    civic_index = snapshot["civic_index"]
    assert civic_index["score"] == 74.0
    assert civic_index["delta"] == 2.0
    assert civic_index["delta_str"] == "+2.0 from yesterday"
