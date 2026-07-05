import re
import time

import requests


class FigmaRateLimitError(Exception):
    """Raised when Figma returns 429 after retries are exhausted."""

    def __init__(self, retry_after=None, limit_type=None, upgrade_link=None):
        self.retry_after = retry_after
        self.limit_type = limit_type
        self.upgrade_link = upgrade_link

        message = "Figma API rate limit exceeded."
        if limit_type == "low":
            message += (
                " Your token is likely tied to a Viewer/Collab seat, which"
                " allows only about 6 file requests per month on Tier 1"
                " endpoints. Use a Full or Dev seat token, or wait until the"
                " limit resets."
            )
        elif retry_after:
            message += f" Try again in about {retry_after} seconds."
        else:
            message += " Wait a minute and try again."

        if upgrade_link:
            message += f" See: {upgrade_link}"

        super().__init__(message)


class FigmaService:

    def __init__(self, api_key):
        self.headers = {
            "X-Figma-Token": api_key
        }
        self.base_url = "https://api.figma.com/v1"

    def get_file(self, file_key, max_retries=2):
        url = f"{self.base_url}/files/{file_key}"

        for attempt in range(max_retries + 1):
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )

            if response.status_code != 429:
                response.raise_for_status()
                return response.json()

            retry_after = int(response.headers.get("Retry-After", 60))
            limit_type = response.headers.get("X-Figma-Rate-Limit-Type")
            upgrade_link = response.headers.get("X-Figma-Upgrade-Link")

            if attempt < max_retries:
                time.sleep(retry_after)
                continue

            raise FigmaRateLimitError(
                retry_after=retry_after,
                limit_type=limit_type,
                upgrade_link=upgrade_link,
            )

    @staticmethod
    def extract_file_key(value):
        """Turn a Figma URL or raw key into a file key."""
        value = (value or "").strip()

        if "figma.com" in value:
            match = re.search(
                r"/(?:file|design)/([a-zA-Z0-9]+)",
                value
            )
            if match:
                return match.group(1)

        return value

    @staticmethod
    def parse_nodes(file_data):
        """Walk the Figma tree and pull out design-relevant info."""
        nodes = []
        document = file_data.get("document", {})

        def walk(node, page_name=""):
            node_type = node.get("type")

            if node_type == "CANVAS":
                page_name = node.get("name", "")

            entry = {
                "id": node.get("id"),
                "name": node.get("name"),
                "type": node_type,
                "page": page_name,
            }

            box = node.get("absoluteBoundingBox")
            if box:
                entry["x"] = round(box.get("x", 0), 1)
                entry["y"] = round(box.get("y", 0), 1)
                entry["width"] = round(box.get("width", 0), 1)
                entry["height"] = round(box.get("height", 0), 1)

            if node_type == "TEXT" and node.get("characters"):
                entry["text"] = node["characters"]

            fills = node.get("fills") or []
            for fill in fills:
                if fill.get("type") == "SOLID" and fill.get("color"):
                    color = fill["color"]
                    entry["fill"] = {
                        "r": round(color.get("r", 0), 2),
                        "g": round(color.get("g", 0), 2),
                        "b": round(color.get("b", 0), 2),
                    }
                    break

            if node_type not in ("DOCUMENT",):
                nodes.append(entry)

            for child in node.get("children", []):
                walk(child, page_name)

        if document:
            walk(document)

        return nodes
