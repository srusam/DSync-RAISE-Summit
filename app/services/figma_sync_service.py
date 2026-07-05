import hashlib
import json

from app import db
from app.models import FigmaFile, FigmaSnapshot
from app.services.design_review_service import DesignReviewService
from app.services.figma_diff_service import FigmaDiffService
from app.services.figma_service import FigmaService


class FigmaSyncService:
    """Fetch Figma file, diff against last snapshot, run AI review."""

    @staticmethod
    def connect(project, file_key, api_key):
        file_key = FigmaService.extract_file_key(file_key)
        figma = FigmaService(api_key)
        file_data = figma.get_file(file_key)
        nodes = FigmaService.parse_nodes(file_data)
        version_hash = FigmaSyncService._hash_nodes(nodes)

        existing = FigmaFile.query.filter_by(
            project_id=project.id,
            file_key=file_key
        ).first()

        if existing:
            figma_file = existing
        else:
            figma_file = FigmaFile(
                project_id=project.id,
                file_key=file_key
            )
            db.session.add(figma_file)

        figma_file.file_name = file_data.get("name")
        figma_file.last_modified = file_data.get("lastModified")

        snapshot = FigmaSnapshot(
            figma_file=figma_file,
            nodes_json=json.dumps(nodes),
            version_hash=version_hash
        )
        db.session.add(snapshot)
        db.session.commit()

        return figma_file

    @staticmethod
    def sync(figma_file, api_key):
        figma = FigmaService(api_key)
        file_data = figma.get_file(figma_file.file_key)
        nodes = FigmaService.parse_nodes(file_data)
        version_hash = FigmaSyncService._hash_nodes(nodes)

        last_snapshot = FigmaSnapshot.query.filter_by(
            figma_file_id=figma_file.id
        ).order_by(
            FigmaSnapshot.created_at.desc()
        ).first()

        if last_snapshot and last_snapshot.version_hash == version_hash:
            return {
                "changed": False,
                "changes": [],
                "insight": None,
                "message": "No changes since last sync.",
            }

        changes = []
        if last_snapshot:
            old_nodes = json.loads(last_snapshot.nodes_json)
            changes = FigmaDiffService.diff_snapshots(old_nodes, nodes)

        figma_file.file_name = file_data.get("name")
        figma_file.last_modified = file_data.get("lastModified")

        snapshot = FigmaSnapshot(
            figma_file_id=figma_file.id,
            nodes_json=json.dumps(nodes),
            version_hash=version_hash
        )
        db.session.add(snapshot)

        insight = None
        if changes:
            insight = DesignReviewService.review_changes(
                figma_file.project_id,
                changes
            )
        else:
            db.session.commit()

        return {
            "changed": bool(changes),
            "changes": changes,
            "insight": insight,
            "message": (
                f"Found {len(changes)} change(s)."
                if changes else "Baseline saved. Make Figma edits, then sync again."
            ),
        }

    @staticmethod
    def _hash_nodes(nodes):
        raw = json.dumps(nodes, sort_keys=True)
        return hashlib.md5(raw.encode()).hexdigest()
