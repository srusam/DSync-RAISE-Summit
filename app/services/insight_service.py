from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app import db
from app.models import AiInsight


class InsightService:

    TZ = ZoneInfo("Asia/Kolkata")

    @staticmethod
    def get_for_project(project_id):
        insights = AiInsight.query.filter_by(
            project_id=project_id
        ).order_by(
            AiInsight.created_at.desc()
        ).all()

        for insight in insights:
            insight.refresh_snooze()

        db.session.commit()
        return insights

    @staticmethod
    def get(insight_id, project_id):
        insight = AiInsight.query.filter_by(
            id=insight_id,
            project_id=project_id
        ).first_or_404()
        insight.refresh_snooze()
        db.session.commit()
        return insight

    @staticmethod
    def acknowledge(insight, note=None):
        insight.status = "acknowledged"
        insight.action_note = (note or "").strip() or None
        insight.action_at = datetime.now(InsightService.TZ)
        insight.snoozed_until = None
        db.session.commit()
        return insight

    @staticmethod
    def dismiss(insight, note=None):
        insight.status = "dismissed"
        insight.action_note = (note or "").strip() or None
        insight.action_at = datetime.now(InsightService.TZ)
        insight.snoozed_until = None
        db.session.commit()
        return insight

    @staticmethod
    def snooze(insight, days=7):
        insight.status = "snoozed"
        insight.action_note = None
        insight.action_at = datetime.now(InsightService.TZ)
        insight.snoozed_until = datetime.now(InsightService.TZ) + timedelta(days=days)
        db.session.commit()
        return insight

    @staticmethod
    def status_label(insight):
        status = insight.refresh_snooze()
        labels = {
            "pending": "Needs review",
            "acknowledged": "Acknowledged",
            "dismissed": "Dismissed",
            "snoozed": "Snoozed",
        }
        return labels.get(status, status)

    @staticmethod
    def is_actionable(insight):
        status = insight.refresh_snooze()
        return status == "pending"
