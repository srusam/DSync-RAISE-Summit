from flask import url_for

from app import db
from app.models import (
    Recording,
    Knowledge,
    Constraint,
    FigmaFile,
    FigmaSnapshot,
    AiInsight,
    DesignHandoff,
    GitHubRepo,
    PullRequest,
)
from app.services.insight_service import InsightService


class TimelineService:
    """Build a unified chronological feed from all project activity."""

    ICONS = {
        "recording": "upload.svg",
        "knowledge": "dashboard.svg",
        "constraint": "register.svg",
        "figma_connect": "chat.svg",
        "figma_sync": "chat.svg",
        "insight": "chat.svg",
        "insight_action": "chat.svg",
        "handoff": "upload.svg",
        "github_connect": "error.svg",
        "pr_analyzed": "error.svg",
    }

    @staticmethod
    def get_events(project_id):
        events = []

        for rec in Recording.query.filter_by(project_id=project_id).all():
            snippet = ""
            if rec.transcript:
                snippet = rec.transcript[:140]
                if len(rec.transcript) > 140:
                    snippet += "…"

            events.append({
                "kind": "recording",
                "at": rec.created_at,
                "title": f"{rec.media_type.title()} recording saved",
                "body": snippet or "Recording stored — transcript pending.",
                "icon": TimelineService.ICONS["recording"],
                "link": url_for("main.recordings", project_id=project_id),
            })

        for entry in Knowledge.query.filter_by(project_id=project_id).all():
            events.append({
                "kind": "knowledge",
                "at": entry.created_at,
                "title": f"Knowledge added: {entry.title}",
                "body": entry.content[:160] + ("…" if len(entry.content) > 160 else ""),
                "icon": TimelineService.ICONS["knowledge"],
                "link": url_for("main.knowledge", project_id=project_id),
            })

        for c in Constraint.query.filter_by(project_id=project_id).all():
            events.append({
                "kind": "constraint",
                "at": c.created_at,
                "title": "Engineer constraint added",
                "body": c.text,
                "icon": TimelineService.ICONS["constraint"],
                "link": url_for("main.constraints_page", project_id=project_id),
            })

        figma_files = FigmaFile.query.filter_by(project_id=project_id).all()
        for ff in figma_files:
            events.append({
                "kind": "figma_connect",
                "at": ff.connected_at,
                "title": f"Figma connected: {ff.file_name or ff.file_key}",
                "body": "Design file linked to project.",
                "icon": TimelineService.ICONS["figma_connect"],
                "link": url_for("main.figma_page", project_id=project_id),
            })

            snapshots = FigmaSnapshot.query.filter_by(
                figma_file_id=ff.id
            ).order_by(
                FigmaSnapshot.created_at.asc()
            ).all()

            for idx, snap in enumerate(snapshots):
                if idx == 0:
                    continue
                events.append({
                    "kind": "figma_sync",
                    "at": snap.created_at,
                    "title": f"Figma synced: {ff.file_name or 'design file'}",
                    "body": "New design snapshot captured.",
                    "icon": TimelineService.ICONS["figma_sync"],
                    "link": url_for("main.figma_page", project_id=project_id),
                })

        insights = AiInsight.query.filter_by(project_id=project_id).all()
        for insight in insights:
            status = insight.refresh_snooze()
            events.append({
                "kind": "insight",
                "at": insight.created_at,
                "title": "AI design alert",
                "body": insight.summary[:200] + ("…" if len(insight.summary) > 200 else ""),
                "icon": TimelineService.ICONS["insight"],
                "link": url_for("main.insights", project_id=project_id),
                "insight_id": insight.id,
                "insight_status": status,
            })

            if insight.action_at and status in ("acknowledged", "dismissed", "snoozed"):
                action_text = InsightService.status_label(insight)
                note = f' — "{insight.action_note}"' if insight.action_note else ""
                if status == "snoozed" and insight.snoozed_until:
                    note = f" until {insight.snoozed_until.strftime('%d %b %Y')}"

                events.append({
                    "kind": "insight_action",
                    "at": insight.action_at,
                    "title": f"Insight {action_text.lower()}",
                    "body": f"Design alert marked as {action_text.lower()}{note}",
                    "icon": TimelineService.ICONS["insight_action"],
                    "link": url_for("main.insights", project_id=project_id),
                    "insight_id": insight.id,
                    "insight_status": status,
                })

        for handoff in DesignHandoff.query.filter_by(
            project_id=project_id,
            status="finalized"
        ).all():
            when = handoff.finalized_at or handoff.created_at
            events.append({
                "kind": "handoff",
                "at": when,
                "title": "Design handoff finalized",
                "body": "Dev spec generated and pushed to engineers.",
                "icon": TimelineService.ICONS["handoff"],
                "link": url_for("main.handoff_page", project_id=project_id),
            })

        for repo in GitHubRepo.query.filter_by(project_id=project_id).all():
            events.append({
                "kind": "github_connect",
                "at": repo.connected_at,
                "title": f"GitHub repo connected: {repo.owner}/{repo.repo_name}",
                "body": "Pull requests will be checked against design.",
                "icon": TimelineService.ICONS["github_connect"],
                "link": url_for("main.github_page", project_id=project_id),
            })

        for pr in PullRequest.query.filter_by(project_id=project_id).all():
            label = "Design PR analyzed" if pr.is_design_change else "PR checked (not design)"
            events.append({
                "kind": "pr_analyzed",
                "at": pr.created_at,
                "title": f"#{pr.pr_number} — {label}",
                "body": pr.title or "Pull request",
                "icon": TimelineService.ICONS["pr_analyzed"],
                "link": url_for("main.github_page", project_id=project_id),
            })

        events.sort(key=lambda e: e["at"], reverse=True)
        db.session.commit()
        return events

    @staticmethod
    def count_pending_insights(project_id):
        count = 0
        for insight in AiInsight.query.filter_by(project_id=project_id).all():
            if InsightService.is_actionable(insight):
                count += 1
        db.session.commit()
        return count
