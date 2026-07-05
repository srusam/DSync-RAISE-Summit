class FigmaDiffService:
    """Compare two Figma snapshots and list what changed."""

    @staticmethod
    def diff_snapshots(old_nodes, new_nodes):
        old_by_id = {
            n["id"]: n for n in old_nodes if n.get("id")
        }
        new_by_id = {
            n["id"]: n for n in new_nodes if n.get("id")
        }

        changes = []

        for node_id, node in new_by_id.items():
            if node_id not in old_by_id:
                changes.append({
                    "change": "added",
                    "node": node,
                })

        for node_id, node in old_by_id.items():
            if node_id not in new_by_id:
                changes.append({
                    "change": "removed",
                    "node": node,
                })

        for node_id in old_by_id:
            if node_id not in new_by_id:
                continue

            old = old_by_id[node_id]
            new = new_by_id[node_id]
            diffs = {}

            for key in set(list(old.keys()) + list(new.keys())):
                if key in ("id", "page"):
                    continue
                if old.get(key) != new.get(key):
                    diffs[key] = {
                        "old": old.get(key),
                        "new": new.get(key),
                    }

            if diffs:
                changes.append({
                    "change": "modified",
                    "node": new,
                    "diffs": diffs,
                })

        return changes

    @staticmethod
    def format_changes(changes):
        """Turn change list into plain text for the AI prompt."""
        if not changes:
            return "No changes detected."

        lines = []

        for item in changes:
            change_type = item["change"]
            node = item["node"]
            label = (
                f"{node.get('name')} ({node.get('type')}) "
                f"on page '{node.get('page')}'"
            )

            if change_type == "added":
                lines.append(f"ADDED: {label}")
            elif change_type == "removed":
                lines.append(f"REMOVED: {label}")
            else:
                lines.append(f"MODIFIED: {label}")
                for field, values in item.get("diffs", {}).items():
                    lines.append(
                        f"  - {field}: {values['old']} → {values['new']}"
                    )

        return "\n".join(lines)
