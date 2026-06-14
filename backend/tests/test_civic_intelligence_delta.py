import pytest
import json
import os
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime, timedelta, timezone

from backend.models import Issue, EscalationAudit, Grievance
from backend.civic_intelligence import CivicIntelligenceEngine

@patch('backend.civic_intelligence.SessionLocal')
@patch('backend.civic_intelligence.trend_analyzer')
@patch('backend.civic_intelligence.adaptive_weights')
@patch('builtins.open', new_callable=mock_open)
@patch('json.dump')
@patch('os.listdir')
def test_civic_intelligence_index_delta(mock_listdir, mock_json_dump, mock_file_open, mock_weights, mock_trend_analyzer, mock_db_session):
    engine = CivicIntelligenceEngine()

    # Mock DB
    mock_session = MagicMock()
    mock_db_session.return_value = mock_session

    # 1. Simulate Previous Snapshot with Score 70.0
    previous_snapshot_content = json.dumps({
        "civic_index": {"score": 70.0},
        "trends": {"category_distribution": {"Fire": 2, "Water": 5}}
    })

    mock_listdir.return_value = ['2023-01-01.json']

    # Mock open to return previous snapshot content when reading
    read_mock = mock_open(read_data=previous_snapshot_content)
    write_mock = mock_open()

    def open_side_effect(file, mode='r', *args, **kwargs):
        if 'r' in mode:
            return read_mock(file, mode, *args, **kwargs)
        return write_mock(file, mode, *args, **kwargs)

    mock_file_open.side_effect = open_side_effect

    # 2. Simulate Current Data for Higher Score
    # Mock Query Results
    mock_query_issues = MagicMock() # For Issues
    mock_query_audits = MagicMock() # For EscalationAudit
    mock_query_grievances = MagicMock() # For Grievances

    def query_side_effect(model):
        if model == Issue:
            return mock_query_issues
        elif model == EscalationAudit:
            return mock_query_audits
        elif model == Grievance:
            return mock_query_grievances
        return MagicMock()

    mock_session.query.side_effect = query_side_effect

    # issues_24h query (new issues)
    # The code calls: db.query(Issue).filter(Issue.created_at >= last_24h).all()
    # And: db.query(Issue).filter(Issue.resolved_at >= last_24h).count()

    # We need to distinguish between the two filter calls or just return something compatible
    # Let's make the first call return a list, and the second a count

    # Configure mock_query_issues to handle chained calls
    # .filter().all() -> returns [Issue, Issue]
    # .filter().count() -> returns 5

    mock_query_issues.filter.return_value.all.return_value = [Issue(id=1), Issue(id=2)]
    mock_query_issues.filter.return_value.count.return_value = 5

    # Mock Escalation Audits (Empty list to avoid iteration error)
    mock_query_audits.filter.return_value.all.return_value = []

    # Setup Trend Analyzer to return a spike
    mock_trend_analyzer.analyze.return_value = {
        "top_keywords": [],
        "category_distribution": {"Fire": 10}, # Spiked from 2
        "clusters": []
    }

    # Mock adaptive weights radius
    mock_weights.get_duplicate_search_radius.return_value = 50.0

    # Run
    engine.run_daily_cycle()

    # Verify Snapshot Content
    # Ensure json.dump was called
    assert mock_json_dump.called
    args, _ = mock_json_dump.call_args
    snapshot = args[0]

    index_data = snapshot['civic_index']

    # Check Score
    # Base 70 + 10 - 1 = 79.0
    assert index_data['score'] == 79.0

    # Check Delta
    # 79.0 - 70.0 = 9.0
    assert index_data['score_delta'] == 9.0

    # Check Emerging Concern
    # Fire increased from 2 to 10 (>50% and >5 items) -> Should be top spike
    assert index_data['top_emerging_concern'] == "Fire"

@patch('backend.civic_intelligence.SessionLocal')
@patch('backend.civic_intelligence.trend_analyzer')
@patch('backend.civic_intelligence.adaptive_weights')
@patch('builtins.open', new_callable=mock_open)
@patch('json.dump')
@patch('os.listdir')
def test_civic_intelligence_no_previous_snapshot(mock_listdir, mock_json_dump, mock_file_open, mock_weights, mock_trend_analyzer, mock_db_session):
    engine = CivicIntelligenceEngine()
    mock_session = MagicMock()
    mock_db_session.return_value = mock_session

    # Simulate NO previous snapshot
    mock_listdir.return_value = []

    # Write mock only
    write_mock = mock_open()
    mock_file_open.side_effect = lambda f, m='r', *a, **k: write_mock(f, m, *a, **k)

    # Mock Query Results
    mock_query_issues = MagicMock() # For Issues
    mock_query_audits = MagicMock() # For EscalationAudit

    def query_side_effect(model):
        if model == Issue:
            return mock_query_issues
        elif model == EscalationAudit:
            return mock_query_audits
        return MagicMock()

    mock_session.query.side_effect = query_side_effect

    # Data: 10 resolved (+20), 0 new (0) => 90.0
    mock_query_issues.filter.return_value.all.return_value = [] # 0 new issues
    mock_query_issues.filter.return_value.count.return_value = 10 # 10 resolved

    mock_query_audits.filter.return_value.all.return_value = []

    mock_trend_analyzer.analyze.return_value = {
        "category_distribution": {"Water": 10}
    }

    # Mock adaptive weights radius (return int/float)
    mock_weights.get_duplicate_search_radius.return_value = 50.0

    engine.run_daily_cycle()

    assert mock_json_dump.called
    args, _ = mock_json_dump.call_args
    snapshot = args[0]
    index_data = snapshot['civic_index']

    assert index_data['score'] == 90.0
    assert index_data['score_delta'] == 0.0 # No previous snapshot, so delta 0

    # Since no previous snapshot, no spike detection base, so fallback to max volume
    assert index_data['top_emerging_concern'] == "Water"
