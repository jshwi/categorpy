from typing import Any, Optional


class Keyring:
    def __init__(self, servicename: str, username: str) -> None:
        self.servicename: str = ...
        self.username: str = ...
        self.headless: bool = ...
        self.password: Optional[str] = ...
        self.saved: bool = ...
        self.entered: int = ...
    def _get_password(self) -> None: ...
    def add_password(self) -> None: ...
    def save_password(self) -> None: ...
