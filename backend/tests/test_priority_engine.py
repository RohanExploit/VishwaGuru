import json
import pytest
import os
from backend.priority_engine import priority_engine

def load_test_data():
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'synthetic_complaints.json')
    with open(data_path, 'r') as f:
        return json.load(f)

test_cases = load_test_data()

@pytest.mark.parametrize("case", test_cases)
def test_priority_engine_logic(case):
    description = case['description']
    result = priority_engine.analyze(description)

    # Check Category
    assert case['expected_category'] in result['suggested_categories'],         f"Failed Category for: {description}. Expected {case['expected_category']}, Got {result['suggested_categories']}"

    # Check Severity - relaxed for minor mismatches in synthetic data vs implementation details
    # We accept if it's within one level if it's subjective, but ideally exact match.
    # For this test suite, we'll keep strict assertion but I've updated the engine to match better.
    assert result['severity'] == case['expected_severity'],         f"Failed Severity for: {description}. Expected {case['expected_severity']}, Got {result['severity']}"

    # Check Urgency
    if 'expected_urgency_min' in case:
        assert result['urgency_score'] >= case['expected_urgency_min'],             f"Failed Urgency Min for: {description}. Expected >= {case['expected_urgency_min']}, Got {result['urgency_score']}"

    if 'expected_urgency_max' in case:
        assert result['urgency_score'] <= case['expected_urgency_max'],             f"Failed Urgency Max for: {description}. Expected <= {case['expected_urgency_max']}, Got {result['urgency_score']}"

def test_explainability():
    description = "Fire in the building, help immediately!"
    result = priority_engine.analyze(description)
    assert len(result['reasoning']) > 0
    # Case insensitive check
    assert any("fire" in r.lower() for r in result['reasoning'])
    assert any("immediately" in r.lower() for r in result['reasoning'])

def test_image_labels_integration():
    description = "There is a problem here."
    labels = ["fire", "smoke"]
    result = priority_engine.analyze(description, image_labels=labels)

    assert result['severity'] == 'Critical'
    assert "Fire" in result['suggested_categories']
