import json

from flask import current_app

from app import db
from app.models import PullRequest, GitHubRepo
from app.services.github_service import GitHubService
from app.services.pr_compare_service import PRCompareService


class PRProcessingService:
    """Fetch a PR, detect design changes, run Figma vs code comparison."""

    @staticmethod
    def connect_repo(project, repo_value):
        owner, repo_name = GitHubService.parse_repo(repo_value)

        existing = GitHubRepo.query.filter_by(
            project_id=project.id,
            owner=owner,
            repo_name=repo_name
        ).first()

        if existing:
            return existing

        repo = GitHubRepo(
            project_id=project.id,
            owner=owner,
            repo_name=repo_name
        )
        db.session.add(repo)
        db.session.commit()
        return repo

    @staticmethod
    def process_pr(project, owner, repo_name, pr_number):
        token = current_app.config.get("GITHUB_TOKEN")
        if not token:
            raise ValueError(
                "GITHUB_TOKEN not set in .env. "
                "Create a PAT at github.com/settings/tokens"
            )

        github = GitHubService(token)
        pr_data = github.get_pull_request(owner, repo_name, pr_number)
        files = github.get_pr_files(owner, repo_name, pr_number)

        is_design = GitHubService.is_design_pr(files)

        existing = PullRequest.query.filter_by(
            project_id=project.id,
            pr_number=pr_number
        ).first()

        if existing:
            pr_record = existing
        else:
            pr_record = PullRequest(
                project_id=project.id,
                pr_number=pr_number
            )
            db.session.add(pr_record)

        pr_record.title = pr_data.get("title")
        pr_record.pr_url = pr_data.get("html_url")
        pr_record.diff_files_json = json.dumps([
            {
                "filename": f.get("filename"),
                "status": f.get("status"),
                "patch": (f.get("patch") or "")[:2000],
            }
            for f in files
        ])
        pr_record.is_design_change = is_design

        if is_design:
            pr_record.mismatch_report = PRCompareService.compare(
                project, files
            )
            pr_record.status = "analyzed"
        else:
            pr_record.mismatch_report = (
                "Not a design-related PR (no UI/style files changed)."
            )
            pr_record.status = "skipped"

        db.session.commit()
        return pr_record

    @staticmethod
    def find_project_for_repo(owner, repo_name):
        github_repo = GitHubRepo.query.filter_by(
            owner=owner,
            repo_name=repo_name
        ).first()
        if github_repo:
            return github_repo.project
        return None
