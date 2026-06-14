"""
Initialize Grievance System
Sets up sample jurisdictions, SLA configurations, and test data.
"""

from backend.database import SessionLocal, engine
from backend.models import Jurisdiction, JurisdictionLevel, SLAConfig, SeverityLevel
from backend.grievance_service import GrievanceService
import json

def initialize_grievance_system():
    """
    Initialize the grievance system with sample data.
    """
    # Create tables
    from backend.models import Base
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Create sample jurisdictions
        jurisdictions_data = [
            {
                "level": JurisdictionLevel.LOCAL,
                "geographic_coverage": {"cities": ["Mumbai"], "districts": ["Mumbai"]},
                "responsible_authority": "Mumbai Municipal Corporation",
                "default_sla_hours": 24
            },
            {
                "level": JurisdictionLevel.DISTRICT,
                "geographic_coverage": {"districts": ["Mumbai", "Pune"], "states": ["Maharashtra"]},
                "responsible_authority": "Maharashtra District Administration",
                "default_sla_hours": 48
            },
            {
                "level": JurisdictionLevel.STATE,
                "geographic_coverage": {"states": ["Maharashtra"]},
                "responsible_authority": "Maharashtra State Government",
                "default_sla_hours": 72
            },
            {
                "level": JurisdictionLevel.NATIONAL,
                "geographic_coverage": {"states": ["Maharashtra", "Karnataka", "Delhi"]},
                "responsible_authority": "Government of India",
                "default_sla_hours": 168  # 1 week
            }
        ]

        for jur_data in jurisdictions_data:
            # Check if jurisdiction already exists
            existing = db.query(Jurisdiction).filter(
                Jurisdiction.level == jur_data["level"],
                Jurisdiction.responsible_authority == jur_data["responsible_authority"]
            ).first()

            if not existing:
                jurisdiction = Jurisdiction(**jur_data)
                db.add(jurisdiction)
                print(f"Created jurisdiction: {jur_data['responsible_authority']}")

        # Create sample SLA configurations
        sla_configs_data = [
            {
                "severity": SeverityLevel.CRITICAL,
                "jurisdiction_level": JurisdictionLevel.LOCAL,
                "department": "health",
                "sla_hours": 4
            },
            {
                "severity": SeverityLevel.HIGH,
                "jurisdiction_level": JurisdictionLevel.DISTRICT,
                "department": "police",
                "sla_hours": 12
            },
            {
                "severity": SeverityLevel.MEDIUM,
                "jurisdiction_level": JurisdictionLevel.STATE,
                "department": "education",
                "sla_hours": 48
            },
            {
                "severity": SeverityLevel.LOW,
                "jurisdiction_level": JurisdictionLevel.NATIONAL,
                "department": "infrastructure",
                "sla_hours": 168
            }
        ]

        for sla_data in sla_configs_data:
            # Check if SLA config already exists
            existing = db.query(SLAConfig).filter(
                SLAConfig.severity == sla_data["severity"],
                SLAConfig.jurisdiction_level == sla_data["jurisdiction_level"],
                SLAConfig.department == sla_data["department"]
            ).first()

            if not existing:
                sla_config = SLAConfig(**sla_data)
                db.add(sla_config)
                print(f"Created SLA config: {sla_data['severity'].value} - {sla_data['department']} - {sla_data['sla_hours']}h")

        db.commit()
        print("Grievance system initialized successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error initializing grievance system: {e}")
    finally:
        db.close()

def test_grievance_creation():
    """
    Test the grievance creation and escalation system.
    """
    service = GrievanceService()

    # Test grievance data
    test_grievances = [
        {
            "category": "health",
            "severity": "critical",
            "city": "Mumbai",
            "district": "Mumbai",
            "state": "Maharashtra",
            "description": "Emergency medical facility needed"
        },
        {
            "category": "police",
            "severity": "high",
            "city": "Pune",
            "district": "Pune",
            "state": "Maharashtra",
            "description": "Security concern in public area"
        },
        {
            "category": "education",
            "severity": "medium",
            "district": "Mumbai",
            "state": "Maharashtra",
            "description": "School infrastructure issue"
        }
    ]

    print("\nTesting grievance creation:")
    for i, grievance_data in enumerate(test_grievances, 1):
        grievance = service.create_grievance(grievance_data)
        if grievance:
            print(f"✓ Created grievance {i}: {grievance.unique_id} - {grievance.category} - {grievance.assigned_authority}")
        else:
            print(f"✗ Failed to create grievance {i}")

if __name__ == "__main__":
    print("Initializing Grievance Escalation System...")
    initialize_grievance_system()
    test_grievance_creation()
    print("\nGrievance system setup complete!")