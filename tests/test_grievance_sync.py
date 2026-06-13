import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Set path
sys.path.append(os.getcwd())

from backend.models import Issue, Grievance, GrievanceStatus, Base, Jurisdiction, JurisdictionLevel
from backend.database import SessionLocal, engine
from backend.grievance_service import GrievanceService
from datetime import datetime, timezone

class TestGrievanceSync(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.db = SessionLocal()
        # Clean up relevant tables
        self.db.query(Grievance).delete()
        self.db.query(Issue).delete()
        self.db.query(Jurisdiction).delete()
        self.db.commit()

        # Create a jurisdiction
        self.jurisdiction = Jurisdiction(
            level=JurisdictionLevel.LOCAL,
            geographic_coverage={"city": "Mumbai"},
            responsible_authority="BMC",
            default_sla_hours=48
        )
        self.db.add(self.jurisdiction)
        self.db.commit()
        self.db.refresh(self.jurisdiction)

    def tearDown(self):
        self.db.close()

    def test_grievance_creation_sync(self):
        # Create an Issue
        issue = Issue(
            description="Test Sync Issue",
            category="pothole",
            status="open",
            latitude=19.0760,
            longitude=72.8777,
            location="Mumbai"
        )
        self.db.add(issue)
        self.db.commit()
        self.db.refresh(issue)

        # Create Grievance linked to Issue
        service = GrievanceService()

        # We need to mock routing service to return our jurisdiction
        with patch("backend.routing_service.RoutingService.determine_initial_jurisdiction") as mock_route, \
             patch("backend.routing_service.RoutingService.assign_authority") as mock_assign:

            mock_route.return_value = self.jurisdiction
            mock_assign.return_value = "Ward Officer"

            grievance_data = {
                "issue_id": issue.id,
                "category": "pothole",
                "severity": "medium",
                "description": "Test Sync Issue",
                "location": {"latitude": 19.0760, "longitude": 72.8777}
            }

            grievance = service.create_grievance(grievance_data, self.db)

            self.assertIsNotNone(grievance)
            self.assertEqual(grievance.issue_id, issue.id)

            # Update Grievance Status -> RESOLVED
            service.update_grievance_status(grievance.id, GrievanceStatus.RESOLVED, self.db)

            # Refresh Issue
            self.db.refresh(issue)

            # Check if Issue status is updated
            self.assertEqual(issue.status, "resolved")
            self.assertIsNotNone(issue.resolved_at)

            # Update Grievance Status -> IN_PROGRESS
            service.update_grievance_status(grievance.id, GrievanceStatus.IN_PROGRESS, self.db)

            self.db.refresh(issue)
            self.assertEqual(issue.status, "in_progress")

if __name__ == "__main__":
    unittest.main()
