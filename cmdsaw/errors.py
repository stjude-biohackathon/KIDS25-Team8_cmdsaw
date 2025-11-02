class CmdSawError(Exception):
    pass

class CommandNotFound(CmdSawError):
    def __init__(self, cmd: str):
        super().__init__(f"Command not found: {cmd}")

class CaptureTimeout(CmdSawError):
    def __init__(self, cmdline: list[str], timeout: int):
        super().__init__(f"Timeout after {timeout}s: {' '.join(cmdline)}")
