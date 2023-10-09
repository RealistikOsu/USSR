from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ScoreSubmissionRequest:
    score_data: str
    visual_settings_b64: str
    updated_beatmap_hash: str
    storyboard_md5: Optional[str]
    iv_b64: str
    unique_ids: str
    score_time: int
    osu_version: str
    client_hash_b64: str
    replay_data_b64: str
    score_id: int
    user_id: int
    osu_auth_token: Optional[str]
    mode_vn: int
    relax: int
