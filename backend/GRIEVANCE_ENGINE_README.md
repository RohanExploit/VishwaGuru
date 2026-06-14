# Multi-Level Grievance Escalation Engine

A comprehensive system for managing grievances with automatic routing, jurisdiction mapping, and SLA-based escalation, similar to real government grievance systems.

## Features

- **Hierarchical Jurisdiction Management**: Local → District → State → National levels
- **Dynamic Routing**: Automatic authority assignment based on geography and department
- **SLA Management**: Configurable SLAs per severity, jurisdiction, and department
- **Automatic Escalation**: SLA breach detection and automatic escalation
- **Audit Trail**: Complete history of all escalations and changes
- **Configurable Rules**: JSON-based configuration for routing and escalation rules

## Architecture

### Core Components

1. **Models** (`models.py`):
   - `Jurisdiction`: Geographic coverage and authority mapping
   - `Grievance`: Core grievance entity with routing information
   - `SLAConfig`: SLA rules configuration
   - `EscalationAudit`: Immutable audit trail

2. **Routing Service** (`routing_service.py`):
   - Determines initial jurisdiction based on geography + department
   - Assigns responsible authorities
   - Manages jurisdiction hierarchy

3. **SLA Configuration Service** (`sla_config_service.py`):
   - Manages SLA rules and calculations
   - Supports configurable SLAs per scenario

4. **Escalation Engine** (`escalation_engine.py`):
   - Evaluates grievances for SLA breaches
   - Performs automatic escalations
   - Handles severity-based escalations

5. **Grievance Service** (`grievance_service.py`):
   - Main interface for grievance operations
   - Integrates all components

## Configuration

### Rules Configuration (`grievance_rules.json`)

```json
{
  "categories": {
    "health": {
      "jurisdiction_level": "district",
      "authority": "District Health Department"
    }
  },
  "geographic_rules": {
    "states": {
      "Maharashtra": {
        "departments": ["health", "education"],
        "default_level": "district"
      }
    }
  },
  "escalation_rules": {
    "auto_escalate_on_sla_breach": true,
    "severity_escalation_threshold": 2
  },
  "sla_defaults": {
    "default_hours": 48
  }
}
```

## Usage

### Initialization

```python
from backend.init_grievance_system import initialize_grievance_system
initialize_grievance_system()
```

### Creating a Grievance

```python
from backend.grievance_service import GrievanceService

service = GrievanceService()

grievance_data = {
    "category": "health",
    "severity": "critical",
    "city": "Mumbai",
    "district": "Mumbai",
    "state": "Maharashtra",
    "description": "Emergency medical facility needed"
}

grievance = service.create_grievance(grievance_data)
print(f"Created grievance: {grievance.unique_id}")
```

### Running Escalation Checks

```python
# Run periodic escalation evaluation
stats = service.run_escalation_check()
print(f"Evaluated: {stats['evaluated']}, Escalated: {stats['escalated']}")
```

### Manual Escalation

```python
# Escalate severity
service.escalate_grievance_severity(grievance_id=1, new_severity="critical")

# Manual escalation
service.manual_escalate(grievance_id=1, reason="Urgent public safety concern")
```

### Getting Audit Trail

```python
audit_trail = service.get_grievance_audit_trail(grievance_id=1)
for entry in audit_trail:
    print(f"{entry['timestamp']}: {entry['previous_authority']} → {entry['new_authority']} ({entry['reason']})")
```

## Database Schema

### Jurisdictions Table
- `id`: Primary key
- `level`: local/district/state/national
- `geographic_coverage`: JSON coverage data
- `responsible_authority`: Authority name
- `default_sla_hours`: Default SLA

### Grievances Table
- `id`: Primary key
- `unique_id`: Public reference ID
- `category`: Department category
- `severity`: low/medium/high/critical
- `pincode/city/district/state`: Geographic location
- `current_jurisdiction_id`: Foreign key to jurisdictions
- `assigned_authority`: Current responsible authority
- `sla_deadline`: SLA deadline timestamp
- `status`: open/in_progress/escalated/resolved
- `created_at/updated_at/resolved_at`: Timestamps

### SLA Configs Table
- `severity`: Severity level
- `jurisdiction_level`: Jurisdiction level
- `department`: Department category
- `sla_hours`: SLA duration

### Escalation Audits Table
- `grievance_id`: Foreign key to grievances
- `previous_authority`: Previous authority
- `new_authority`: New authority
- `timestamp`: Escalation timestamp
- `reason`: sla_breach/severity_upgrade/manual
- `notes`: Additional context

## SLA Calculation Logic

1. **Exact Match**: severity + jurisdiction + department
2. **Department + Severity**: department + severity (any jurisdiction)
3. **Severity + Jurisdiction**: severity + jurisdiction (any department)
4. **Severity Only**: severity (any jurisdiction/department)
5. **Default**: configured default hours

## Escalation Rules

### Automatic Escalation Triggers
- **SLA Breach**: When current time > SLA deadline
- **Severity Upgrade**: When severity increases significantly (configurable threshold)

### Escalation Process
1. Determine next jurisdiction level
2. Find appropriate jurisdiction for new level
3. Reassign authority
4. Recalculate SLA for new jurisdiction
5. Create audit log entry
6. Update grievance status

### Prevention
- Cannot escalate beyond national level
- Idempotent operations prevent duplicate escalations

## Extension Points

- **AI-based Priority**: Add ML service for dynamic priority assessment
- **Manual Overrides**: Extend audit logs for override reasons
- **Notification System**: Add notification service for escalations
- **Custom Rules**: Extend rules engine for complex routing logic
- **Integration APIs**: REST API endpoints for external systems

## Testing

Run the initialization script to set up sample data and test the system:

```bash
python backend/init_grievance_system.py
```

This will:
- Create sample jurisdictions
- Set up SLA configurations
- Test grievance creation
- Verify routing and assignment logic