from __future__ import annotations

from dataclasses import dataclass

import config
from app.constants.privileges import Privileges


@dataclass
class User:
    id: int
    name: str
    privileges: Privileges
    friends: list[int]
    password_bcrypt: str
    country: str
    vanilla_pp_leaderboards: bool

    def __repr__(self) -> str:
        return f"<{self.name} ({self.id})>"

    @property
    def url(self) -> str:
        # i hate this
        server_url = config.SRV_URL.replace("https://", "").replace("http://", "")

        return f"https://{server_url}/u/{self.id}"

    @property
    def embed(self) -> str:
        return f"[{self.url} {self.name}]"
