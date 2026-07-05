from app import db
from app.models import Constraint


class ConstraintService:

    @staticmethod
    def add(project, text):
        constraint = Constraint(
            project_id=project.id,
            text=text.strip()
        )
        db.session.add(constraint)
        db.session.commit()
        return constraint

    @staticmethod
    def delete(constraint):
        db.session.delete(constraint)
        db.session.commit()

    @staticmethod
    def list_for_project(project_id):
        return Constraint.query.filter_by(
            project_id=project_id
        ).order_by(
            Constraint.created_at.desc()
        ).all()
