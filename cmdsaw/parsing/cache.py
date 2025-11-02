from __future__ import annotations
import hashlib, json, os

class ParseCache:
    """
    Disk-based cache for LLM parse results.

    Stores parsed command documentation on disk to avoid redundant LLM calls
    for the same command and help text. Cache keys are based on command path,
    version, model name, and help text hash.
    """
    def __init__(self, root: str | None = None):
        """
        Initialize the parse cache.

        :param root: Optional cache directory root (defaults to ~/.cache/cmdsaw)
        :type root: str | None
        """
        self.root = root or os.path.join(os.path.expanduser("~"), ".cache", "cmdsaw")
        os.makedirs(self.root, exist_ok=True)

    def _key_path(self, command_path: str, version: str | None, model: str, help_hash: str) -> str:
        """
        Generate a cache file path for given cache parameters.

        :param command_path: Full command path
        :type command_path: str
        :param version: Command version or None
        :type version: str | None
        :param model: Model name used for parsing
        :type model: str
        :param help_hash: SHA256 hash of the help text
        :type help_hash: str
        :return: Absolute path to the cache file
        :rtype: str
        """
        base = f"{command_path}|{version or 'none'}|{model}|{help_hash}"
        h = hashlib.sha256(base.encode()).hexdigest()[:32]
        return os.path.join(self.root, f"{h}.json")

    def get(self, command_path: str, version: str | None, model: str, help_text: str) -> dict | None:
        """
        Retrieve cached parse result if it exists.

        :param command_path: Full command path
        :type command_path: str
        :param version: Command version or None
        :type version: str | None
        :param model: Model name used for parsing
        :type model: str
        :param help_text: Raw help text
        :type help_text: str
        :return: Cached parse result dict, or None if not cached
        :rtype: dict | None
        """
        help_hash = hashlib.sha256(help_text.encode()).hexdigest()
        p = self._key_path(command_path, version, model, help_hash)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def set(self, command_path: str, version: str | None, model: str, help_text: str, data: dict) -> None:
        """
        Store a parse result in the cache.

        :param command_path: Full command path
        :type command_path: str
        :param version: Command version or None
        :type version: str | None
        :param model: Model name used for parsing
        :type model: str
        :param help_text: Raw help text
        :type help_text: str
        :param data: Parse result dictionary to cache
        :type data: dict
        :return: None
        :rtype: None
        """
        help_hash = hashlib.sha256(help_text.encode()).hexdigest()
        p = self._key_path(command_path, version, model, help_hash)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
