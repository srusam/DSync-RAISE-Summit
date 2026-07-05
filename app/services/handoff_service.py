import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app import db
from app.models import DesignHandoff, FigmaFile, FigmaSnapshot, Constraint
from app.services.ai_service import AIService
from app.services.context_service import ContextService


class HandoffService:

    SYSTEM_PROMPT = """You are a senior front-end engineer writing a design handoff document.
Write clear, actionable specs an engineer can code from.

Include these sections:
1. Overview — what this design is
2. Components — list each UI element with size, color, text
3. Layout — spacing, positions, responsive notes
4. Engineer Constraints — rules engineers must follow (from constraints list)
5. Do NOT — things to avoid based on past knowledge

Use markdown headings. Be specific with pixel values and colors from the Figma data."""

    @staticmethod
    def finalize(project):
        figma_file = FigmaFile.query.filter_by(
            project_id=project.id
        ).order_by(
            FigmaFile.connected_at.desc()
        ).first()

        if not figma_file:
            raise ValueError(
                "Connect a Figma file first (Figma page → Connect)."
            )

        snapshot = FigmaSnapshot.query.filter_by(
            figma_file_id=figma_file.id
        ).order_by(
            FigmaSnapshot.created_at.desc()
        ).first()

        if not snapshot:
            raise ValueError(
                "No Figma snapshot found. Sync your Figma file first."
            )

        nodes = json.loads(snapshot.nodes_json)
        figma_summary = HandoffService._summarize_nodes(nodes)

        constraints = Constraint.query.filter_by(
            project_id=project.id
        ).all()
        constraints_text = "\n".join(
            f"- {c.text}" for c in constraints
        ) or "None added yet."

        context = ContextService.build_context(project.id)

        user_prompt = f"""PROJECT: {project.title}
{project.description or ''}

FIGMA FILE: {figma_file.file_name}
FIGMA COMPONENTS:
{figma_summary}

ENGINEER CONSTRAINTS:
{constraints_text}

PROJECT KNOWLEDGE & HISTORY:
{context}

Generate a complete engineer handoff spec for this design."""

        spec = AIService.chat(
            HandoffService.SYSTEM_PROMPT,
            user_prompt,
            temperature=0.2
        )

        handoff = DesignHandoff(
            project_id=project.id,
            figma_snapshot_id=snapshot.id,
            spec=spec,
            status="finalized",
            finalized_at=datetime.now(ZoneInfo("Asia/Kolkata"))
        )

        db.session.add(handoff)
        db.session.commit()

        return handoff

    @staticmethod
    def get_latest(project_id):
        return DesignHandoff.query.filter_by(
            project_id=project_id,
            status="finalized"
        ).order_by(
            DesignHandoff.finalized_at.desc()
        ).first()

    @staticmethod
    def _summarize_nodes(nodes, limit=40):
        """Keep prompt size manageable — summarize key design nodes."""
        important = []

        for node in nodes:
            if node.get("type") in (
                "FRAME", "COMPONENT", "INSTANCE", "TEXT", "RECTANGLE", "BUTTON"
            ):
                important.append(node)

        if not important:
            important = nodes[:limit]
        else:
            important = important[:limit]

        lines = []
        for n in important:
            parts = [
                f"{n.get('name')} ({n.get('type')})",
                f"page={n.get('page')}",
            ]
            if n.get("width"):
                parts.append(
                    f"{n.get('width')}x{n.get('height')}px"
                )
            if n.get("text"):
                parts.append(f"text=\"{n.get('text')[:80]}\"")
            if n.get("fill"):
                c = n["fill"]
                parts.append(
                    f"color=rgb({c.get('r')},{c.get('g')},{c.get('b')})"
                )
            lines.append(" | ".join(parts))

        return "\n".join(lines) if lines else "No design nodes parsed."
