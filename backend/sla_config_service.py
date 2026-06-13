"""
Grievance Escalation Engine - SLA Configuration Service
Manages SLA rules and configurations for different scenarios.
"""

from typing import Optional
from sqlalchemy.orm import Session
from backend.models import SLAConfig, JurisdictionLevel, SeverityLevel
from backend.database import SessionLocal

class SLAConfigService:
    """
    Service for managing SLA configurations and calculating deadlines.
    """

    def __init__(self, default_sla_hours: int = 48):
        """
        Initialize SLA service with default SLA.

        Args:
            default_sla_hours: Default SLA in hours if no specific config found
        """
        self.default_sla_hours = default_sla_hours

    def get_sla_hours(self, severity: SeverityLevel, jurisdiction_level: JurisdictionLevel,
                     department: str, db: Session = None) -> int:
        """
        Get SLA hours for specific combination of severity, jurisdiction, and department.

        Args:
            severity: Severity level
            jurisdiction_level: Jurisdiction level
            department: Department/category
            db: Database session

        Returns:
            SLA hours
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            # Try to find exact match
            sla_config = db.query(SLAConfig).filter(
                SLAConfig.severity == severity,
                SLAConfig.jurisdiction_level == jurisdiction_level,
                SLAConfig.department == department
            ).first()

            if sla_config:
                return sla_config.sla_hours

            # Try department and severity only
            sla_config = db.query(SLAConfig).filter(
                SLAConfig.severity == severity,
                SLAConfig.department == department,
                SLAConfig.jurisdiction_level.is_(None)
            ).first()

            if sla_config:
                return sla_config.sla_hours

            # Try severity and jurisdiction only
            sla_config = db.query(SLAConfig).filter(
                SLAConfig.severity == severity,
                SLAConfig.jurisdiction_level == jurisdiction_level,
                SLAConfig.department.is_(None)
            ).first()

            if sla_config:
                return sla_config.sla_hours

            # Try severity only
            sla_config = db.query(SLAConfig).filter(
                SLAConfig.severity == severity,
                SLAConfig.jurisdiction_level.is_(None),
                SLAConfig.department.is_(None)
            ).first()

            if sla_config:
                return sla_config.sla_hours

            # Return default
            return self.default_sla_hours

        finally:
            if should_close:
                db.close()

    def create_sla_config(self, severity: SeverityLevel, jurisdiction_level: JurisdictionLevel,
                         department: str, sla_hours: int, db: Session = None) -> SLAConfig:
        """
        Create a new SLA configuration.

        Args:
            severity: Severity level
            jurisdiction_level: Jurisdiction level
            department: Department/category
            sla_hours: SLA in hours
            db: Database session

        Returns:
            Created SLAConfig object
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            sla_config = SLAConfig(
                severity=severity,
                jurisdiction_level=jurisdiction_level,
                department=department,
                sla_hours=sla_hours
            )

            db.add(sla_config)
            db.commit()
            db.refresh(sla_config)

            return sla_config

        finally:
            if should_close:
                db.close()

    def get_all_sla_configs(self, db: Session = None) -> list[SLAConfig]:
        """
        Get all SLA configurations.

        Args:
            db: Database session

        Returns:
            List of SLAConfig objects
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            return db.query(SLAConfig).all()

        finally:
            if should_close:
                db.close()