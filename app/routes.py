from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from app.forms import ProjectForm
from app.models import Project
from app.services.project_service import ProjectService

from app.models import Knowledge
from app.forms import KnowledgeForm
from app.services.knowledge_service import KnowledgeService

import os

from werkzeug.utils import secure_filename

from flask import request, redirect, flash

from flask import current_app
from app import db
from app.models import Recording

from flask import request
from werkzeug.utils import secure_filename
import os
import uuid
from flask import abort

from app.services.transcription_service import TranscriptionService

from flask import current_app, jsonify, request
from app.services.figma_sync_service import FigmaSyncService
from app.services.figma_service import FigmaRateLimitError
from app.models import FigmaFile, AiInsight
from app.models import Constraint, DesignHandoff
from app.forms import ConstraintForm
from app.services.constraint_service import ConstraintService
from app.services.handoff_service import HandoffService
from app.forms import GitHubConnectForm
from app.services.pr_processing_service import PRProcessingService
from app.models import GitHubRepo, PullRequest
from app.services.timeline_service import TimelineService
from app.services.insight_service import InsightService

import hashlib
import hmac


def _get_project(project_id):
    return Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()


def _redirect_back(project_id, fallback="main.project"):
    target = request.referrer
    if target:
        return redirect(target)
    return redirect(url_for(fallback, project_id=project_id))

main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template("index.html")


@main.route("/dashboard")
@login_required
def dashboard():

    projects = Project.query.filter_by(
        user_id=current_user.id
    ).order_by(Project.created_at.desc()).all()

    return render_template(
        "dashboard.html",
        projects=projects
    )


@main.route("/projects/create", methods=["GET", "POST"])
@login_required
def create_project():

    form = ProjectForm()

    if form.validate_on_submit():

        ProjectService.create_project(
            title=form.title.data,
            description=form.description.data,
            user=current_user
        )

        return redirect(url_for("main.dashboard"))

    return render_template(
        "create_project.html",
        form=form
    )
    
@main.route("/project/<int:project_id>/delete", methods=["POST"])
@login_required
def delete_project(project_id):

    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(project)
    db.session.commit()

    return redirect(url_for("main.dashboard"))
    
@main.route("/project/<int:project_id>")
@login_required
def project(project_id):

    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    recordings = Recording.query.filter_by(
        project_id=project.id
    ).order_by(
        Recording.created_at.desc()
    ).all()

    pending_insights = TimelineService.count_pending_insights(project.id)

    return render_template(
        "project.html",
        project=project,
        recordings=recordings,
        pending_insights=pending_insights
    )
    
@main.route("/project/<int:project_id>/knowledge")
@login_required
def knowledge(project_id):

    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    entries = Knowledge.query.filter_by(
        project_id=project.id
    ).order_by(
        Knowledge.created_at.desc()
    ).all()

    return render_template(
        "knowledge.html",
        project=project,
        entries=entries
    )
    
@main.route("/project/<int:project_id>/knowledge/new",
            methods=["GET","POST"])
@login_required
def add_knowledge(project_id):

    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    form = KnowledgeForm()

    if form.validate_on_submit():

        KnowledgeService.add_entry(
            project,
            form.title.data,
            form.content.data
        )

        return redirect(
            url_for(
                "main.knowledge",
                project_id=project.id
            )
        )

    return render_template(
        "add_knowledge.html",
        form=form,
        project=project
    )


@main.route("/project/<int:project_id>/upload", methods=["POST"])
@login_required
def upload_recording(project_id):

    project = Project.query.get_or_404(project_id)

    file = request.files.get("recording")

    if not file:

        flash("No file selected.", "danger")

        return redirect(
            url_for("main.project", project_id=project.id)
        )

    filename = secure_filename(file.filename)

    save_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        "recordings",
        filename
        
    )
    
    
    file.save(save_path)

    recording = Recording(
        filename=filename,
        original_name=file.filename,
        project=project
    )

    db.session.add(recording)

    db.session.commit()

    flash("Recording uploaded!", "success")

    return redirect(
        url_for("main.project", project_id=project.id)
    )
    
@main.route(
    "/project/<int:project_id>/record",
    methods=["GET", "POST"]
)
@login_required
def record(project_id):

    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()
    media_type = request.args.get("type", "audio")
    print(media_type)

    if request.method == "POST":
        print("POST RECEIVED")

        media = request.files["media"]

        extension = "webm"
        filename = f"{uuid.uuid4()}.{extension}"

        folder = os.path.join(
            "uploads",
            "recordings"
        )

        os.makedirs(folder, exist_ok=True)

        filepath = os.path.join(
            folder,
            filename
        )

        media.save(filepath)
        import traceback

        try:
            transcript = TranscriptionService.transcribe(filepath)
        except Exception:
            traceback.print_exc()
            transcript = ""
       
        
        recording = Recording(

            title=f"{media_type.title()} Recording",
            media_type=media_type,
            file_path=filename,
            transcript=transcript,
            transcript_status="Ready",
            project_id=project.id
        )
       
        print(filepath)
        db.session.add(recording)
        db.session.commit()
        print("Saved to database")

        return redirect(
            url_for(
                "main.project",
                project_id=project.id
            )
        )
  

    # ← GET requests come here
    return render_template(
        "record_recording.html",
        project=project,
        media_type=media_type
    )
    
from flask import send_from_directory

@main.route("/uploads/recordings/<filename>")
def uploaded_recording(filename):

    import os
    from flask import current_app

    UPLOAD_FOLDER = os.path.join(
        current_app.root_path,
        "..",
        "uploads",
        "recordings"
    )

    return send_from_directory(
        os.path.abspath(UPLOAD_FOLDER),
        filename
    )
    
@main.route("/project/<int:project_id>/recordings")
@login_required
def recordings(project_id):

    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    recordings = Recording.query.filter_by(
        project_id=project.id
    ).order_by(
        Recording.created_at.desc()
    ).all()

    return render_template(
        "recordings.html",
        project=project,
        recordings=recordings
    )
    
@main.route("/recording/<int:recording_id>/delete", methods=["POST"])
@login_required
def delete_recording(recording_id):

    recording = Recording.query.get_or_404(recording_id)

    if recording.project.user_id != current_user.id:
        abort(403)

    filepath = os.path.join(
        "uploads",
        "recordings",
        recording.file_path
    )

    if os.path.exists(filepath):
        os.remove(filepath)

    project_id = recording.project_id

    db.session.delete(recording)
    db.session.commit()

    return redirect(
        url_for(
            "main.recordings",
            project_id=project_id
        )
    )
    
@main.route("/project/<int:project_id>/figma/connect", methods=["POST"])
@login_required
def connect_figma(project_id):

    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    data = request.get_json() or {}
    file_key = data.get("file_key") or data.get("figma_url")

    if not file_key:
        return jsonify({
            "success": False,
            "message": "Figma URL or file key is required."
        }), 400

    try:
        figma_file = FigmaSyncService.connect(
            project,
            file_key,
            current_app.config["FIGMA_API_KEY"]
        )

        return jsonify({
            "success": True,
            "file_name": figma_file.file_name,
            "file_key": figma_file.file_key,
            "last_modified": figma_file.last_modified,
            "message": "Figma file connected. Edit in Figma, then click Sync."
        })

    except FigmaRateLimitError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 429

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@main.route("/project/<int:project_id>/figma")
@login_required
def figma_page(project_id):

    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    figma_file = FigmaFile.query.filter_by(
        project_id=project.id
    ).order_by(
        FigmaFile.connected_at.desc()
    ).first()

    insights = InsightService.get_for_project(project.id)

    return render_template(
        "figma.html",
        project=project,
        figma_file=figma_file,
        insights=insights
    )


@main.route("/project/<int:project_id>/figma/sync", methods=["POST"])
@login_required
def sync_figma(project_id):

    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    figma_file = FigmaFile.query.filter_by(
        project_id=project.id
    ).order_by(
        FigmaFile.connected_at.desc()
    ).first()

    if not figma_file:
        return jsonify({
            "success": False,
            "message": "Connect a Figma file first."
        }), 400

    try:
        result = FigmaSyncService.sync(
            figma_file,
            current_app.config["FIGMA_API_KEY"]
        )

        insight_data = None
        if result.get("insight"):
            insight = result["insight"]
            insight_data = {
                "id": insight.id,
                "summary": insight.summary,
                "status": insight.status or "pending",
                "created_at": insight.created_at.strftime("%Y-%m-%d %H:%M"),
            }

        return jsonify({
            "success": True,
            "changed": result["changed"],
            "change_count": len(result["changes"]),
            "message": result["message"],
            "insight": insight_data,
        })

    except FigmaRateLimitError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 429

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@main.route("/project/<int:project_id>/insights")
@login_required
def insights(project_id):

    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    insights = InsightService.get_for_project(project.id)

    return render_template(
        "insights.html",
        project=project,
        insights=insights
    )


@main.route("/project/<int:project_id>/timeline")
@login_required
def timeline(project_id):

    project = _get_project(project_id)
    events = TimelineService.get_events(project.id)
    pending_count = TimelineService.count_pending_insights(project.id)

    return render_template(
        "timeline.html",
        project=project,
        events=events,
        pending_count=pending_count
    )


@main.route(
    "/project/<int:project_id>/insights/<int:insight_id>/acknowledge",
    methods=["POST"]
)
@login_required
def acknowledge_insight(project_id, insight_id):

    _get_project(project_id)
    insight = InsightService.get(insight_id, project_id)
    note = request.form.get("note", "")
    InsightService.acknowledge(insight, note)
    flash("Insight acknowledged.", "success")
    return _redirect_back(project_id)


@main.route(
    "/project/<int:project_id>/insights/<int:insight_id>/dismiss",
    methods=["POST"]
)
@login_required
def dismiss_insight(project_id, insight_id):

    _get_project(project_id)
    insight = InsightService.get(insight_id, project_id)
    note = request.form.get("note", "")
    InsightService.dismiss(insight, note)
    flash("Insight dismissed.", "info")
    return _redirect_back(project_id)


@main.route(
    "/project/<int:project_id>/insights/<int:insight_id>/snooze",
    methods=["POST"]
)
@login_required
def snooze_insight(project_id, insight_id):

    _get_project(project_id)
    insight = InsightService.get(insight_id, project_id)
    InsightService.snooze(insight, days=7)
    flash("Insight snoozed for 7 days.", "info")
    return _redirect_back(project_id)


@main.route("/project/<int:project_id>/constraints", methods=["GET", "POST"])
@login_required
def constraints_page(project_id):

    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    form = ConstraintForm()

    if form.validate_on_submit():
        ConstraintService.add(project, form.text.data)
        flash("Constraint added.", "success")
        return redirect(
            url_for("main.constraints_page", project_id=project.id)
        )

    constraints = ConstraintService.list_for_project(project.id)

    return render_template(
        "constraints.html",
        project=project,
        form=form,
        constraints=constraints
    )


@main.route(
    "/project/<int:project_id>/constraints/<int:constraint_id>/delete",
    methods=["POST"]
)
@login_required
def delete_constraint(project_id, constraint_id):

    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    constraint = Constraint.query.filter_by(
        id=constraint_id,
        project_id=project.id
    ).first_or_404()

    ConstraintService.delete(constraint)
    flash("Constraint removed.", "success")

    return redirect(
        url_for("main.constraints_page", project_id=project.id)
    )


@main.route("/project/<int:project_id>/handoff", methods=["GET"])
@login_required
def handoff_page(project_id):

    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    figma_file = FigmaFile.query.filter_by(
        project_id=project.id
    ).order_by(
        FigmaFile.connected_at.desc()
    ).first()

    handoff = HandoffService.get_latest(project.id)
    constraints = ConstraintService.list_for_project(project.id)

    figma_embed_url = None
    if figma_file:
        figma_embed_url = (
            f"https://www.figma.com/embed?"
            f"embed_host=share&url="
            f"https://www.figma.com/design/{figma_file.file_key}"
        )

    return render_template(
        "handoff.html",
        project=project,
        figma_file=figma_file,
        handoff=handoff,
        constraints=constraints,
        figma_embed_url=figma_embed_url
    )


@main.route("/project/<int:project_id>/handoff/finalize", methods=["POST"])
@login_required
def finalize_handoff(project_id):

    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    try:
        HandoffService.finalize(project)
        flash(
            "Design finalized and pushed to engineers!",
            "success"
        )
    except Exception as e:
        flash(str(e), "danger")

    return redirect(
        url_for("main.handoff_page", project_id=project.id)
    )


@main.route("/project/<int:project_id>/github", methods=["GET", "POST"])
@login_required
def github_page(project_id):

    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    form = GitHubConnectForm()

    if form.validate_on_submit():
        try:
            PRProcessingService.connect_repo(
                project,
                form.repo_url.data
            )
            flash("GitHub repo connected.", "success")
        except Exception as e:
            flash(str(e), "danger")
        return redirect(
            url_for("main.github_page", project_id=project.id)
        )

    github_repo = GitHubRepo.query.filter_by(
        project_id=project.id
    ).order_by(
        GitHubRepo.connected_at.desc()
    ).first()

    pull_requests = PullRequest.query.filter_by(
        project_id=project.id
    ).order_by(
        PullRequest.created_at.desc()
    ).all()

    return render_template(
        "github.html",
        project=project,
        form=form,
        github_repo=github_repo,
        pull_requests=pull_requests
    )


@main.route("/project/<int:project_id>/github/check", methods=["POST"])
@login_required
def check_github_pr(project_id):

    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    github_repo = GitHubRepo.query.filter_by(
        project_id=project.id
    ).first()

    if not github_repo:
        flash("Connect a GitHub repo first.", "danger")
        return redirect(
            url_for("main.github_page", project_id=project.id)
        )

    pr_number = request.form.get("pr_number", type=int)
    if not pr_number:
        flash("Enter a valid PR number.", "danger")
        return redirect(
            url_for("main.github_page", project_id=project.id)
        )

    try:
        pr_record = PRProcessingService.process_pr(
            project,
            github_repo.owner,
            github_repo.repo_name,
            pr_number
        )
        if pr_record.is_design_change:
            flash(
                f"PR #{pr_number} analyzed — design changes detected.",
                "success"
            )
        else:
            flash(
                f"PR #{pr_number} checked — not a design PR.",
                "info"
            )
    except Exception as e:
        flash(str(e), "danger")

    return redirect(
        url_for("main.github_page", project_id=project.id)
    )


@main.route("/webhooks/github", methods=["POST"])
def github_webhook():
    """GitHub sends PR events here. No login required."""

    payload = request.get_data()
    signature = request.headers.get("X-Hub-Signature-256", "")
    secret = current_app.config.get("GITHUB_WEBHOOK_SECRET")

    if secret:
        expected = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return jsonify({"error": "Invalid signature"}), 403

    event = request.headers.get("X-GitHub-Event", "")
    data = request.get_json(silent=True) or {}

    if event != "pull_request":
        return jsonify({"status": "ignored", "reason": "not a PR event"})

    action = data.get("action")
    if action not in ("opened", "synchronize", "reopened"):
        return jsonify({"status": "ignored", "reason": f"action={action}"})

    pr = data.get("pull_request", {})
    repo = data.get("repository", {})
    full_name = repo.get("full_name", "")

    if "/" not in full_name:
        return jsonify({"error": "no repo"}), 400

    owner, repo_name = full_name.split("/", 1)
    pr_number = pr.get("number")

    project = PRProcessingService.find_project_for_repo(owner, repo_name)
    if not project:
        return jsonify({"status": "ignored", "reason": "repo not linked"})

    try:
        PRProcessingService.process_pr(
            project, owner, repo_name, pr_number
        )
        return jsonify({"status": "ok", "pr": pr_number})
    except Exception as e:
        return jsonify({"error": str(e)}), 500