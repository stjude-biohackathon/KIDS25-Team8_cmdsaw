from __future__ import annotations
import hashlib, json, os

class ParseCache:
    def __init__(self, root: str | None = None):
        self.root = root or os.path.join(os.path.expanduser("~"), ".cache", "cmdsaw")
        os.makedirs(self.root, exist_ok=True)

    def _key_path(self, command_path: str, version: str | None, model: str, help_hash: str) -> str:
        base = f"{command_path}|{version or 'none'}|{model}|{help_hash}"
        h = hashlib.sha256(base.encode()).hexdigest()[:32]
        return os.path.join(self.root, f"{h}.json")

    def get(self, command_path: str, version: str | None, model: str, help_text: str) -> dict | None:
        help_hash = hashlib.sha256(help_text.encode()).hexdigest()
        p = self._key_path(command_path, version, model, help_hash)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def set(self, command_path: str, version: str | None, model: str, help_text: str, data: dict) -> None:
        help_hash = hashlib.sha256(help_text.encode()).hexdigest()
        p = self._key_path(command_path, version, model, help_hash)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
