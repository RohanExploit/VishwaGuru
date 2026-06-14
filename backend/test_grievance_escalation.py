"""
Test Grievance Escalation Engine
Demonstrates the escalation functionality.
"""

from backend.grievance_service import GrievanceService
from backend.models import SeverityLevel
from datetime import datetime, timezone, timedelta

def test_escalation():
    """Test the escalation engine functionality."""
    service = GrievanceService()

    print("=== Grievance Escalation Engine Test ===\n")

    # Create a test grievance
    grievance_data = {
        "category": "health",
        "severity": "high",
        "city": "Mumbai",
        "district": "Mumbai",
        "state": "Maharashtra",
        "description": "Medical emergency response needed"
    }

    grievance = service.create_grievance(grievance_data)
    if not grievance:
        print("Failed to create grievance")
        return

    # Refresh to load relationships
    grievance = service.get_grievance(grievance.id)
    if not grievance:
        print("Failed to retrieve grievance")
        return

    print(f"Created grievance: {grievance.unique_id}")
    print(f"Initial jurisdiction: {grievance.jurisdiction.level.value}")
    print(f"Assigned authority: {grievance.assigned_authority}")
    print(f"SLA deadline: {grievance.sla_deadline}")
    print()

    # Test severity escalation
    print("Testing severity escalation...")
    success = service.escalate_grievance_severity(
        grievance.id,
        SeverityLevel.CRITICAL,
        "Emergency situation escalated"
    )

    if success:
        # Refresh grievance data
        updated_grievance = service.get_grievance(grievance.id)
        print(f"✓ Severity escalated to: {updated_grievance.severity.value}")
        print(f"New SLA deadline: {updated_grievance.sla_deadline}")
    else:
        print("✗ Severity escalation failed")

    print()

    # Test manual escalation
    print("Testing manual escalation...")
    success = service.manual_escalate(grievance.id, "Urgent manual escalation required")

    if success:
        # Refresh grievance data
        updated_grievance = service.get_grievance(grievance.id)
        print(f"✓ Manually escalated to: {updated_grievance.jurisdiction.level.value}")
        print(f"New authority: {updated_grievance.assigned_authority}")
    else:
        print("✗ Manual escalation failed")

    print()

    # Show audit trail
    print("Audit Trail:")
    audit_trail = service.get_grievance_audit_trail(grievance.id)
    for i, entry in enumerate(audit_trail, 1):
        print(f"{i}. {entry['timestamp'][:19]}: {entry['previous_authority']} → {entry['new_authority']}")
        print(f"   Reason: {entry['reason']}, Notes: {entry.get('notes', 'N/A')}")

    print()

    # Test SLA breach simulation (by manually setting old deadline)
    print("Testing SLA breach escalation...")
    # Note: In real scenario, this would be done by the periodic escalation check
    # For demo, we'll manually trigger escalation check
    stats = service.run_escalation_check()
    print(f"Escalation check results: Evaluated {stats['evaluated']}, Escalated {stats['escalated']}")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_escalation()