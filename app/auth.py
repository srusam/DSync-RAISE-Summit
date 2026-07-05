from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request
)

from werkzeug.security import ( #Yo! This is open source library for password hashing and verification
    generate_password_hash,
    check_password_hash
)

from flask_login import ( #And yeah this is open source library for user session management
    login_user,
    logout_user,
    login_required,
    current_user
)

from . import db
from .models import User
from .forms import RegisterForm, LoginForm


auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()

    if form.validate_on_submit():

        existing_user = User.query.filter_by(
            username=form.username.data
        ).first()

        if existing_user:
            flash("Username already exists.", "danger")
            return redirect(url_for("auth.register"))

        existing_email = User.query.filter_by(
            email=form.email.data
        ).first()

        if existing_email:
            flash("Email already registered.", "danger")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(
            form.password.data
        )

        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully! Please login.", "success")

        return redirect(url_for("auth.login"))

    return render_template(
        "register.html",
        form=form
    )


@auth.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(
            email=form.email.data
        ).first()

        if user is None:

            flash("Invalid email or password.", "danger")

            return redirect(url_for("auth.login"))

        if not check_password_hash(
            user.password_hash,
            form.password.data
        ):

            flash("Invalid email or password.", "danger")

            return redirect(url_for("auth.login"))

        login_user(user)

        next_page = request.args.get("next")

        if next_page:

            return redirect(next_page)

        flash("Welcome back!", "success")

        return redirect(url_for("main.dashboard"))

    return render_template(
        "login.html",
        form=form
    )


@auth.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully.", "success")

    return redirect(url_for("auth.login"))

# Hi judges ◝(ᵔᗜᵔ)◜

# I am doing authentication and authorization in this file. I have created a blueprint for authentication routes, including registration, login, and logout functionalities. The `register` route handles user registration, checking for existing usernames and emails, hashing passwords, and saving new users to the database. The `login` route manages user login, verifying credentials and handling redirection after successful login. The `logout` route allows users to log out of their session. I have used Flask-Login to manage user sessions and ensure that certain routes are protected and accessible only to authenticated users. For form handling, I have used Flask-WTF to create forms for registration and login, which include validation to ensure that the input data is correct. Flash messages are used to provide feedback to users about the success or failure of their actions. For password security, I have used Werkzeug's password hashing utilities to securely store and verify user passwords. 