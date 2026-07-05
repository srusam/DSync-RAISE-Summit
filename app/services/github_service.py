import re

import requests


DESIGN_EXTENSIONS = (
    ".css", ".scss", ".sass", ".less",
    ".tsx", ".jsx", ".vue", ".html",
    ".styled.ts", ".module.css",
)

DESIGN_PATH_KEYWORDS = (
    "components/", "component/", "styles/", "style/",
    "ui/", "pages/", "views/", "layout/", "assets/",
)


class GitHubService:

    def __init__(self, token):
        self.token = token
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    @staticmethod
    def parse_repo(value):
        """Parse owner/repo from URL or raw string."""
        value = (value or "").strip().rstrip("/")

        if "github.com" in value:
            match = re.search(
                r"github\.com/([^/]+)/([^/#?]+)",
                value
            )
            if match:
                return match.group(1), match.group(2).replace(".git", "")

        if "/" in value:
            parts = value.split("/")
            return parts[0], parts[1].replace(".git", "")

        raise ValueError(
            "Invalid repo. Use owner/repo or https://github.com/owner/repo"
        )

    def get_pull_request(self, owner, repo, pr_number):
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        response = requests.get(
            url, headers=self.headers, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def get_pr_files(self, owner, repo, pr_number):
        url = (
            f"https://api.github.com/repos/{owner}/{repo}"
            f"/pulls/{pr_number}/files"
        )
        response = requests.get(
            url, headers=self.headers, timeout=30
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def is_design_pr(files):
        """True if PR touches UI/style files."""
        for f in files:
            filename = (f.get("filename") or "").lower()
            if any(filename.endswith(ext) for ext in DESIGN_EXTENSIONS):
                return True
            if any(kw in filename for kw in DESIGN_PATH_KEYWORDS):
                return True
        return False

    @staticmethod
    def format_diff(files, max_patch_len=1500):
        """Format PR file diffs for the AI prompt."""
        lines = []

        for f in files:
            filename = f.get("filename", "unknown")
            status = f.get("status", "modified")
            patch = f.get("patch") or "(binary or too large)"

            if len(patch) > max_patch_len:
                patch = patch[:max_patch_len] + "\n... (truncated)"

            lines.append(f"FILE: {filename} ({status})\n{patch}")

        return "\n\n---\n\n".join(lines) if lines else "No diff available."
