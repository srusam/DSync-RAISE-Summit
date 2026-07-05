import requests

FIGMA_BASE = "https://api.figma.com/v1"

class FigmaService:
    def __init__(self, token):
        self.headers = {
            "X-Figma-Token": token
        }

    def get_file(self, file_key):
        url = f"{FIGMA_BASE}/files/{file_key}"
        res = requests.get(url, headers=self.headers)
        return res.json()

    def get_file_nodes(self, file_key, node_ids):
        url = f"{FIGMA_BASE}/files/{file_key}/nodes"
        params = {"ids": ",".join(node_ids)}
        res = requests.get(url, headers=self.headers, params=params)
        return res.json()