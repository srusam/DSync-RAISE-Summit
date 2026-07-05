from datetime import datetime
from zoneinfo import ZoneInfo
from flask_login import UserMixin


from . import db


class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(
            ZoneInfo("Asia/Kolkata")
        )
    )

    chats = db.relationship(
        "Chat",
        backref="user",
        cascade="all, delete-orphan"
    )

    uploaded_files = db.relationship(
        "UploadedFile",
        backref="user",
        cascade="all, delete-orphan"
    )
    
    projects = db.relationship(
        "Project",
        backref="owner",
        lazy=True,
        cascade="all, delete-orphan"
    )

from datetime import datetime

class Project(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(150), nullable=False)

    description = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(
            ZoneInfo("Asia/Kolkata")
        )
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(
            ZoneInfo("Asia/Kolkata")
        )
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    
    knowledge = db.relationship(
        "Knowledge",
        backref="project",
        lazy=True,
        cascade="all, delete-orphan"
    )
    
    recordings = db.relationship(
        "Recording",
        backref="project",
        cascade="all, delete-orphan",
        lazy=True
    )

    figma_files = db.relationship(
        "FigmaFile",
        backref="project",
        cascade="all, delete-orphan",
        lazy=True
    )

    ai_insights = db.relationship(
        "AiInsight",
        backref="project",
        cascade="all, delete-orphan",
        lazy=True
    )

    constraints = db.relationship(
        "Constraint",
        backref="project",
        cascade="all, delete-orphan",
        lazy=True
    )

    design_handoffs = db.relationship(
        "DesignHandoff",
        backref="project",
        cascade="all, delete-orphan",
        lazy=True
    )

    github_repos = db.relationship(
        "GitHubRepo",
        backref="project",
        cascade="all, delete-orphan",
        lazy=True
    )

    pull_requests = db.relationship(
        "PullRequest",
        backref="project",
        cascade="all, delete-orphan",
        lazy=True
    )


class Knowledge(db.Model):

    __tablename__ = "knowledge"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(200),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    source = db.Column(
        db.String(50),
        default="manual"
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(
            ZoneInfo("Asia/Kolkata")
        )
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("project.id"),
        nullable=False
    )

from . import login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Chat(db.Model):

    __tablename__ = "chats"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(255),
        default="New Chat"
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(
            ZoneInfo("Asia/Kolkata")
        )
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    messages = db.relationship(
        "Message",
        backref="chat",
        cascade="all, delete-orphan"
    )


class Message(db.Model):

    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)

    role = db.Column(
        db.String(20)
    )

    content = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(
            ZoneInfo("Asia/Kolkata")
        )
    )

    chat_id = db.Column(
        db.Integer,
        db.ForeignKey("chats.id"),
        nullable=False
    )


class UploadedFile(db.Model):

    __tablename__ = "uploaded_files"

    id = db.Column(db.Integer, primary_key=True)

    filename = db.Column(
        db.String(255)
    )

    filepath = db.Column(
        db.String(500)
    )

    uploaded_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(
                ZoneInfo("Asia/Kolkata")
        )
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    
    
class Recording(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(150), nullable=False)

    media_type = db.Column(
        db.String(20),
        nullable=False
    )       # audio / video

    file_path = db.Column(
        db.String(300),
        nullable=False
    )

    transcript = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(
            ZoneInfo("Asia/Kolkata")
        )
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("project.id"),
        nullable=False
    )
    
    transcript_status = db.Column(
        db.String(20),
        default="Pending"
    )
    
class Constraint(db.Model):

    __tablename__ = "constraint"

    id = db.Column(db.Integer, primary_key=True)

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("project.id"),
        nullable=False
    )

    text = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Kolkata"))
    )


class FigmaFile(db.Model):

    __tablename__ = "figma_file"

    id = db.Column(db.Integer, primary_key=True)

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("project.id"),
        nullable=False
    )

    file_key = db.Column(db.String(100), nullable=False)

    file_name = db.Column(db.String(255))

    last_modified = db.Column(db.String(50))

    connected_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Kolkata"))
    )

    snapshots = db.relationship(
        "FigmaSnapshot",
        backref="figma_file",
        cascade="all, delete-orphan",
        lazy=True
    )


class FigmaSnapshot(db.Model):

    __tablename__ = "figma_snapshot"

    id = db.Column(db.Integer, primary_key=True)

    figma_file_id = db.Column(
        db.Integer,
        db.ForeignKey("figma_file.id"),
        nullable=False
    )

    nodes_json = db.Column(db.Text, nullable=False)

    version_hash = db.Column(db.String(64))

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Kolkata"))
    )


class AiInsight(db.Model):

    __tablename__ = "ai_insight"

    id = db.Column(db.Integer, primary_key=True)

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("project.id"),
        nullable=False
    )

    insight_type = db.Column(
        db.String(50),
        default="design_change"
    )

    summary = db.Column(db.Text, nullable=False)

    sources_json = db.Column(db.Text)

    changes_json = db.Column(db.Text)

    status = db.Column(
        db.String(20),
        default="pending"
    )

    action_note = db.Column(db.Text)

    action_at = db.Column(db.DateTime)

    snoozed_until = db.Column(db.DateTime)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Kolkata"))
    )

    def refresh_snooze(self):
        """Return effective status; auto-clear expired snoozes."""
        if not self.status:
            self.status = "pending"

        if self.status != "snoozed" or not self.snoozed_until:
            return self.status
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
        snooze_end = self.snoozed_until
        if snooze_end.tzinfo is None:
            snooze_end = snooze_end.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
        if now >= snooze_end:
            self.status = "pending"
            self.snoozed_until = None
            return "pending"
        return "snoozed"


class DesignHandoff(db.Model):

    __tablename__ = "design_handoff"

    id = db.Column(db.Integer, primary_key=True)

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("project.id"),
        nullable=False
    )

    figma_snapshot_id = db.Column(
        db.Integer,
        db.ForeignKey("figma_snapshot.id"),
        nullable=True
    )

    spec = db.Column(db.Text, nullable=False)

    status = db.Column(
        db.String(20),
        default="draft"
    )

    finalized_at = db.Column(db.DateTime)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Kolkata"))
    )

    figma_snapshot = db.relationship("FigmaSnapshot", backref="handoffs")


class GitHubRepo(db.Model):

    __tablename__ = "github_repo"

    id = db.Column(db.Integer, primary_key=True)

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("project.id"),
        nullable=False
    )

    owner = db.Column(db.String(100), nullable=False)

    repo_name = db.Column(db.String(100), nullable=False)

    connected_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Kolkata"))
    )


class PullRequest(db.Model):

    __tablename__ = "pull_request"

    id = db.Column(db.Integer, primary_key=True)

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("project.id"),
        nullable=False
    )

    pr_number = db.Column(db.Integer, nullable=False)

    title = db.Column(db.String(500))

    pr_url = db.Column(db.String(500))

    diff_files_json = db.Column(db.Text)

    is_design_change = db.Column(db.Boolean, default=False)

    mismatch_report = db.Column(db.Text)

    status = db.Column(db.String(20), default="pending")

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Kolkata"))
    )