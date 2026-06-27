"""CRM state machine for application status tracking."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from src.db.models import Application, ApplicationStatus, JobPosting, User


class CRMStateMachine:
    """Manages application status transitions and pipeline tracking."""

    # Valid status transitions
    TRANSITIONS = {
        ApplicationStatus.SAVED: [
            ApplicationStatus.APPLIED,
            ApplicationStatus.WITHDRAWN,
        ],
        ApplicationStatus.APPLIED: [
            ApplicationStatus.PHONE_SCREEN,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        ],
        ApplicationStatus.PHONE_SCREEN: [
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        ],
        ApplicationStatus.INTERVIEW: [
            ApplicationStatus.OFFER,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        ],
        ApplicationStatus.OFFER: [
            ApplicationStatus.WITHDRAWN,  # Declined offer
        ],
        ApplicationStatus.REJECTED: [],
        ApplicationStatus.WITHDRAWN: [],
    }

    def __init__(self, db: Session):
        self.db = db

    def can_transition(
        self,
        application: Application,
        new_status: ApplicationStatus
    ) -> bool:
        """Check if a status transition is valid."""
        current = application.status
        allowed = self.TRANSITIONS.get(current, [])
        return new_status in allowed

    def transition(
        self,
        application: Application,
        new_status: ApplicationStatus,
        notes: Optional[str] = None
    ) -> Application:
        """Transition an application to a new status."""
        if not self.can_transition(application, new_status):
            raise ValueError(
                f"Cannot transition from {application.status.value} to {new_status.value}"
            )

        application.status = new_status
        application.last_activity_at = datetime.utcnow()

        if notes:
            if application.notes:
                application.notes += f"\n\n[{datetime.utcnow().isoformat()}] {notes}"
            else:
                application.notes = f"[{datetime.utcnow().isoformat()}] {notes}"

        # Track interview rounds
        if new_status == ApplicationStatus.INTERVIEW:
            application.interview_rounds += 1

        # Set applied_at timestamp
        if new_status == ApplicationStatus.APPLIED and not application.applied_at:
            application.applied_at = datetime.utcnow()

        self.db.flush()
        return application

    def create_application(
        self,
        user: User,
        job: JobPosting,
        initial_status: ApplicationStatus = ApplicationStatus.SAVED
    ) -> Application:
        """Create a new application."""
        # Check if application already exists
        existing = self.db.query(Application).filter(
            Application.user_id == user.id,
            Application.job_id == job.id,
        ).first()

        if existing:
            return existing

        application = Application(
            user_id=user.id,
            job_id=job.id,
            status=initial_status,
        )

        if initial_status == ApplicationStatus.APPLIED:
            application.applied_at = datetime.utcnow()

        self.db.add(application)
        self.db.flush()
        return application

    def get_pipeline_stats(self, user: User) -> dict:
        """Get pipeline statistics for a user."""
        applications = self.db.query(Application).filter(
            Application.user_id == user.id
        ).all()

        stats = {status.value: 0 for status in ApplicationStatus}
        for app in applications:
            stats[app.status.value] += 1

        # Calculate rates
        total = len(applications)
        applied = sum(1 for a in applications if a.status != ApplicationStatus.SAVED)
        interviews = sum(1 for a in applications if a.status in [
            ApplicationStatus.PHONE_SCREEN,
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.OFFER,
        ])
        offers = stats[ApplicationStatus.OFFER.value]

        return {
            "by_status": stats,
            "total": total,
            "applied": applied,
            "interviews": interviews,
            "offers": offers,
            "response_rate": (interviews / applied * 100) if applied > 0 else 0,
            "offer_rate": (offers / interviews * 100) if interviews > 0 else 0,
        }

    def get_stale_applications(
        self,
        user: User,
        days_threshold: int = 7
    ) -> List[Application]:
        """Get applications that haven't been updated recently."""
        from datetime import timedelta

        threshold = datetime.utcnow() - timedelta(days=days_threshold)

        # Active statuses that shouldn't be stale
        active_statuses = [
            ApplicationStatus.APPLIED,
            ApplicationStatus.PHONE_SCREEN,
            ApplicationStatus.INTERVIEW,
        ]

        stale = self.db.query(Application).filter(
            Application.user_id == user.id,
            Application.status.in_(active_statuses),
            Application.last_activity_at < threshold,
        ).all()

        return stale
