from __future__ import annotations

from dataclasses import dataclass

import settings
from app.constants.privileges import Privileges


@dataclass
class User:
    id: int
    name: str
    privileges: Privileges
    friends: list[int]
    password_bcrypt: str
    country: str
    coins: int

    def __repr__(self) -> str:
        return f"<{self.name} ({self.id})>"

    @property
    def url(self) -> str:
        # i hate this
        server_url = settings.PS_DOMAIN.replace("https://", "").replace("http://", "")

        return f"https://{server_url}/u/{self.id}"

    @property
    def embed(self) -> str:
        return f"[{self.url} {self.name}]"
