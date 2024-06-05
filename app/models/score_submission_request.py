from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScoreSubmissionRequest:
    score_data: str
    exited_out: bool
    fail_time: int
    visual_settings_b64: str
    updated_beatmap_hash: str
    storyboard_md5: str | None
    iv_b64: str
    unique_ids: str
    score_time: int
    osu_version: str
    client_hash_b64: str
    score_id: int
    user_id: int
    osu_auth_token: str | None
    mode_vn: int
    relax: int
