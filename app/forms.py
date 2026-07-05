from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import PasswordField
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import EqualTo
from wtforms.validators import Length


class RegisterForm(FlaskForm):

    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3,max=30)
        ]
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email()
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=6)
        ]
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password")
        ]
    )

    submit = SubmitField("Create Account")


class LoginForm(FlaskForm):

    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email()
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired()
        ]
    )

    submit = SubmitField("Login")
    
class ProjectForm(FlaskForm):

    title = StringField(
        "Project Title",
        validators=[DataRequired()]
    )

    description = TextAreaField(
        "Description"
    )

    submit = SubmitField(
        "Create Project"
    )
    
class KnowledgeForm(FlaskForm):

    title = StringField(
        "Title",
        validators=[DataRequired()]
    )

    content = TextAreaField(
        "Content",
        validators=[DataRequired()]
    )

    submit = SubmitField("Save")


class ConstraintForm(FlaskForm):

    text = TextAreaField(
        "Constraint",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "e.g. CTA button must stay rectangular, max 5 nav items..."
        }
    )

    submit = SubmitField("Add Constraint")


class GitHubConnectForm(FlaskForm):

    repo_url = StringField(
        "GitHub Repository",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "https://github.com/owner/repo or owner/repo"
        }
    )

    submit = SubmitField("Connect Repo")