"""
Grievance Escalation Engine - Routing Service
Handles dynamic routing and authority assignment based on geography and department.
"""

import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.models import Jurisdiction, JurisdictionLevel, Grievance
from backend.database import SessionLocal

class RoutingService:
    """
    Service for determining jurisdiction and authority assignment for grievances.
    Uses configurable rules to route grievances to appropriate authorities.
    """

    def __init__(self, rules_config: Dict[str, Any]):
        """
        Initialize with routing rules configuration.

        Args:
            rules_config: Dictionary containing routing rules
        """
        self.rules_config = rules_config

    def determine_initial_jurisdiction(self, grievance_data: Dict[str, Any], db: Session) -> Optional[Jurisdiction]:
        """
        Determine the initial jurisdiction for a grievance based on geography and department.

        Routing logic:
        1. Check for specific geographic rules (pincode/city/district/state)
        2. Match against department-specific rules
        3. Fall back to default jurisdiction level

        Args:
            grievance_data: Dictionary containing grievance details
            db: Database session

        Returns:
            Jurisdiction object or None if no match found
        """
        category = grievance_data.get('category')
        pincode = grievance_data.get('pincode')
        city = grievance_data.get('city')
        district = grievance_data.get('district')
        state = grievance_data.get('state')

        # Get routing rules for the category
        category_rules = self.rules_config.get('categories', {}).get(category, {})
        geographic_rules = self.rules_config.get('geographic_rules', {})

        # Check for state-level rules
        if state and state in geographic_rules.get('states', {}):
            state_config = geographic_rules['states'][state]
            if category in state_config.get('departments', []):
                jurisdiction_level = JurisdictionLevel.STATE
            else:
                jurisdiction_level = state_config.get('default_level', JurisdictionLevel.DISTRICT)
        else:
            # Default to district level for known states, local for others
            jurisdiction_level = JurisdictionLevel.DISTRICT if state else JurisdictionLevel.LOCAL

        # Override based on category-specific rules
        if 'jurisdiction_level' in category_rules:
            jurisdiction_level = JurisdictionLevel(category_rules['jurisdiction_level'])

        # Find the specific jurisdiction
        jurisdiction = self._find_jurisdiction(
            jurisdiction_level=jurisdiction_level,
            state=state,
            district=district,
            city=city,
            db=db
        )

        return jurisdiction

    def assign_authority(self, jurisdiction: Jurisdiction, category: str) -> str:
        """
        Assign the responsible authority based on jurisdiction and category.

        Args:
            jurisdiction: Jurisdiction object
            category: Grievance category/department

        Returns:
            Authority name
        """
        # Check category-specific authority overrides
        category_rules = self.rules_config.get('categories', {}).get(category, {})
        if 'authority' in category_rules:
            return category_rules['authority']

        # Use jurisdiction's default authority
        return jurisdiction.responsible_authority

    def _find_jurisdiction(self, jurisdiction_level: JurisdictionLevel, state: Optional[str] = None,
                          district: Optional[str] = None, city: Optional[str] = None,
                          db: Session = None) -> Optional[Jurisdiction]:
        """
        Find the most specific jurisdiction matching the given criteria.

        Args:
            jurisdiction_level: Level of jurisdiction to find
            state: State name
            district: District name
            city: City name
            db: Database session

        Returns:
            Matching Jurisdiction or None
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            # Query for jurisdictions matching the criteria
            query = db.query(Jurisdiction).filter(Jurisdiction.level == jurisdiction_level)

            jurisdictions = query.all()

            # Find the best match based on geographic coverage
            best_match = None
            best_match_score = 0

            for jur in jurisdictions:
                coverage = jur.geographic_coverage
                score = 0

                if state and state in coverage.get('states', []):
                    score += 3
                if district and district in coverage.get('districts', []):
                    score += 2
                if city and city in coverage.get('cities', []):
                    score += 1

                if score > best_match_score:
                    best_match = jur
                    best_match_score = score

            return best_match

        finally:
            if should_close:
                db.close()

    def get_next_jurisdiction_level(self, current_level: JurisdictionLevel) -> Optional[JurisdictionLevel]:
        """
        Get the next higher jurisdiction level for escalation.

        Args:
            current_level: Current jurisdiction level

        Returns:
            Next jurisdiction level or None if at top level
        """
        level_hierarchy = {
            JurisdictionLevel.LOCAL: JurisdictionLevel.DISTRICT,
            JurisdictionLevel.DISTRICT: JurisdictionLevel.STATE,
            JurisdictionLevel.STATE: JurisdictionLevel.NATIONAL,
            JurisdictionLevel.NATIONAL: None
        }

        return level_hierarchy.get(current_level)

    def can_escalate(self, current_level: JurisdictionLevel) -> bool:
        """
        Check if escalation is possible from current level.

        Args:
            current_level: Current jurisdiction level

        Returns:
            True if escalation is possible
        """
        return self.get_next_jurisdiction_level(current_level) is not None