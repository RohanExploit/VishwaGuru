import logging
import json
import os
from pywebpush import webpush, WebPushException
from backend.database import SessionLocal
from backend.models import Issue, PushSubscription
from backend.cache import recent_issues_cache
from backend.ai_service import generate_action_plan, build_x_post
from backend.grievance_service import GrievanceService
from backend.schemas import IssueSummaryResponse

logger = logging.getLogger(__name__)

async def process_action_plan_background(issue_id: int, description: str, category: str, language: str, image_path: str):
    db = SessionLocal()
    try:
        # Generate Action Plan (AI)
        action_plan = await generate_action_plan(description, category, language, image_path)

        # Update issue in DB
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if issue:
            current_plan = issue.action_plan or {}
            issue.action_plan = {**current_plan, **action_plan}
            db.commit()

            # Invalidate cache to ensure users get the updated action plan
            recent_issues_cache.clear()
    except Exception as e:
        logger.error(f"Background action plan generation failed for issue {issue_id}: {e}", exc_info=True)
    finally:
        db.close()

async def create_grievance_from_issue_background(issue_id: int):
    """Background task to create a grievance from an issue for escalation management"""
    db = SessionLocal()
    try:
        # Get the issue
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            logger.error(f"Issue {issue_id} not found for grievance creation")
            return

        # Get grievance service
        grievance_service = GrievanceService()

        # Map issue category to grievance severity
        severity_mapping = {
            'pothole': 'high',
            'garbage': 'medium',
            'streetlight': 'medium',
            'flood': 'critical',
            'infrastructure': 'high',
            'parking': 'low',
            'fire': 'critical',
            'animal': 'medium',
            'blocked': 'high',
            'tree': 'medium',
            'pest': 'low',
            'vandalism': 'medium'
        }

        severity = severity_mapping.get(issue.category.lower(), 'medium')

        # Create grievance data
        grievance_data = {
            'issue_id': issue.id,
            'category': issue.category,
            'severity': severity,
            'pincode': None,  # Will be determined by routing service
            'description': issue.description,
            'location': {
                'latitude': issue.latitude,
                'longitude': issue.longitude,
                'address': issue.location
            },
            'reporter_info': {
                'email': issue.user_email,
                'source': issue.source
            }
        }

        # Create grievance
        grievance = grievance_service.create_grievance(grievance_data, db)
        if grievance:
            logger.info(f"Created grievance {grievance.id} from issue {issue_id}")
        else:
            logger.error(f"Failed to create grievance from issue {issue_id}")

    except Exception as e:
        logger.error(f"Error creating grievance from issue {issue_id}: {e}", exc_info=True)
    finally:
        db.close()

def send_status_notification(issue_id: int, old_status: str, new_status: str, notes: str = None):
    """Send push notification for issue status update"""
    db = SessionLocal()
    try:
        # Get issue details
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            return

        # Get subscriptions for this issue or general subscriptions
        subscriptions = db.query(PushSubscription).filter(
            (PushSubscription.issue_id == issue_id) | (PushSubscription.issue_id.is_(None))
        ).all()

        # VAPID keys (in production, these should be environment variables)
        vapid_private_key = os.getenv("VAPID_PRIVATE_KEY", "dev_private_key")
        vapid_public_key = os.getenv("VAPID_PUBLIC_KEY", "dev_public_key")
        vapid_email = os.getenv("VAPID_EMAIL", "mailto:test@example.com")

        status_messages = {
            "verified": "Your issue has been verified by authorities",
            "assigned": f"Your issue has been assigned to {issue.assigned_to or 'authorities'}",
            "in_progress": "Work on your issue has begun",
            "resolved": "Your issue has been resolved!"
        }

        message = status_messages.get(new_status, f"Your issue status changed to {new_status}")

        payload = {
            "title": "Issue Update",
            "body": message,
            "icon": "/icon-192.png",
            "badge": "/icon-192.png",
            "data": {
                "issue_id": issue_id,
                "status": new_status,
                "url": f"/issue/{issue_id}"
            }
        }

        for subscription in subscriptions:
            try:
                webpush(
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": {
                            "p256dh": subscription.p256dh,
                            "auth": subscription.auth
                        }
                    },
                    data=json.dumps(payload),
                    vapid_private_key=vapid_private_key,
                    vapid_claims={
                        "sub": vapid_email
                    }
                )
            except WebPushException as e:
                logger.error(f"Failed to send push notification: {e}")
                # Remove invalid subscriptions
                if e.response.status_code in [400, 404, 410]:
                    db.delete(subscription)

        db.commit()

    except Exception as e:
        logger.error(f"Error sending status notification: {e}")
    finally:
        db.close()
