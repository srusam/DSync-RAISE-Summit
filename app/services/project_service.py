from app.models import db, Project


class ProjectService:

    @staticmethod
    def create_project(title, description, user):

        project = Project(
            title=title,
            description=description,
            owner=user
        )

        db.session.add(project)
        db.session.commit()

        return project