import json

from app.models import FigmaFile, FigmaSnapshot, DesignHandoff
from app.services.ai_service import AIService
from app.services.github_service import GitHubService
from app.services.handoff_service import HandoffService


class PRCompareService:
    """Compare a PR code diff against the finalized Figma design."""

    SYSTEM_PROMPT = """You are a design QA engineer.
Compare the GitHub PR code changes against the Figma design spec.

Your job:
1. Say if the code matches the design (yes/no/mpartial)
2. List specific mismatches (colors, sizes, layout, missing elements)
3. Give actionable fix suggestions for the engineer
4. Reference the handoff spec when relevant

Be concise. Use bullet points. Start with a one-line verdict."""

    @staticmethod
    def compare(project, pr_files):
        design_context = PRCompareService._get_design_context(project)
        diff_text = GitHubService.format_diff(pr_files)

        user_prompt = f"""DESIGN SPEC / FIGMA DATA:
{design_context}

PR CODE CHANGES:
{diff_text}

Does this PR match the design? List mismatches and suggestions."""

        return AIService.chat(
            PRCompareService.SYSTEM_PROMPT,
            user_prompt,
            temperature=0.2
        )

    @staticmethod
    def _get_design_context(project):
        handoff = HandoffService.get_latest(project.id)
        if handoff:
            return f"FINALIZED HANDOFF SPEC:\n{handoff.spec}"

        figma_file = FigmaFile.query.filter_by(
            project_id=project.id
        ).order_by(
            FigmaFile.connected_at.desc()
        ).first()

        if not figma_file:
            return "No Figma file or handoff available."

        snapshot = FigmaSnapshot.query.filter_by(
            figma_file_id=figma_file.id
        ).order_by(
            FigmaSnapshot.created_at.desc()
        ).first()

        if not snapshot:
            return f"Figma file connected ({figma_file.file_name}) but no snapshot."

        nodes = json.loads(snapshot.nodes_json)
        summary = HandoffService._summarize_nodes(nodes, limit=30)

        return (
            f"FIGMA FILE: {figma_file.file_name}\n"
            f"DESIGN NODES:\n{summary}"
        )
