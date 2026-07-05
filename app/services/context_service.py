from app.models import Knowledge, Recording, Constraint


class ContextService:
    """Gathers project knowledge, transcripts, and constraints for AI prompts."""

    @staticmethod
    def build_context(project_id, query=None):
        """
        Collect all text the AI should know about for a project.

        Args:
            project_id: Which project to pull data from.
            query:      Optional search term — only include entries that mention it.
                        If None, include everything (fine for small projects).

        Returns:
            str — formatted block of text ready to paste into an AI prompt.
        """
        sections = []

        # --- Knowledge base entries ---
        knowledge_entries = Knowledge.query.filter_by(
            project_id=project_id
        ).order_by(Knowledge.created_at.desc()).all()

        if knowledge_entries:
            lines = ["=== KNOWLEDGE BASE ==="]
            for entry in knowledge_entries:
                block = f"[{entry.created_at.strftime('%Y-%m-%d')}] {entry.title}\n{entry.content}"
                if query and not ContextService._matches(query, block):
                    continue
                lines.append(block)
            if len(lines) > 1:
                sections.append("\n\n".join(lines))

        # --- Recording transcripts ---
        recordings = Recording.query.filter_by(
            project_id=project_id
        ).filter(
            Recording.transcript.isnot(None),
            Recording.transcript != "",
        ).order_by(Recording.created_at.desc()).all()

        if recordings:
            lines = ["=== MEETING TRANSCRIPTS ==="]
            for rec in recordings:
                block = (
                    f"[{rec.created_at.strftime('%Y-%m-%d')}] "
                    f"{rec.title} ({rec.media_type})\n{rec.transcript}"
                )
                if query and not ContextService._matches(query, block):
                    continue
                lines.append(block)
            if len(lines) > 1:
                sections.append("\n\n".join(lines))

        # --- Engineer constraints ---
        constraints = Constraint.query.filter_by(
            project_id=project_id
        ).order_by(Constraint.created_at.desc()).all()

        if constraints:
            lines = ["=== ENGINEER CONSTRAINTS ==="]
            for c in constraints:
                block = f"[{c.created_at.strftime('%Y-%m-%d')}] {c.text}"
                if query and not ContextService._matches(query, block):
                    continue
                lines.append(block)
            if len(lines) > 1:
                sections.append("\n\n".join(lines))

        if not sections:
            return "No project context available yet."

        return "\n\n".join(sections)

    @staticmethod
    def _matches(query, text):
        """Simple case-insensitive keyword check (good enough for hackathon)."""
        if not query:
            return True
        query_lower = query.lower()
        text_lower = text.lower()
        return any(
            word in text_lower
            for word in query_lower.split()
            if len(word) > 2
        )
