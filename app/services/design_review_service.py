import json

from app import db
from app.models import AiInsight
from app.services.ai_service import AIService
from app.services.context_service import ContextService
from app.services.figma_diff_service import FigmaDiffService


class DesignReviewService:
    """Compare Figma changes against project knowledge and generate AI alerts."""

    SYSTEM_PROMPT = """You are a design advisor for a product team.
You receive:
1) Past knowledge, meeting transcripts, and engineer constraints
2) Recent Figma design changes

Your job:
- Flag if a change conflicts with past findings or constraints
- Reference specific past dates or sources when relevant
- Be concise and actionable (2-4 short paragraphs max)
- If nothing relevant in the knowledge base, say so briefly
- Start with "Heads up:" when warning about a conflict"""

    @staticmethod
    def review_changes(project_id, changes):
        if not changes:
            return None

        changes_text = FigmaDiffService.format_changes(changes)

        query = " ".join(
            item["node"].get("name", "")
            for item in changes
            if item.get("node", {}).get("name")
        )

        context = ContextService.build_context(project_id, query=query)
        if context == "No project context available yet.":
            context = ContextService.build_context(project_id)

        user_prompt = f"""PROJECT CONTEXT:
{context}

RECENT FIGMA CHANGES:
{changes_text}

Analyze these design changes against the project context.
Mention specific dates or sources from the knowledge base when relevant."""

        summary = AIService.chat(
            DesignReviewService.SYSTEM_PROMPT,
            user_prompt
        )

        insight = AiInsight(
            project_id=project_id,
            insight_type="design_change",
            summary=summary,
            changes_json=json.dumps(changes),
            sources_json=json.dumps({
                "query": query,
                "change_count": len(changes),
            }),
        )

        db.session.add(insight)
        db.session.commit()

        return insight
