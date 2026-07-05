from app import db
from app.models import Knowledge


class KnowledgeService:

    @staticmethod
    def add_entry(project, title, content):

        entry = Knowledge(
            title=title,
            content=content,
            project=project
        )

        db.session.add(entry)
        db.session.commit()

        return entry