from dataclasses import dataclass
from typing import Optional


@dataclass
class ScoreSubmissionRequest:
    score_data: bytes
    exited_out: bool
    fail_time: int
    visual_settings_b64: bytes
    updated_beatmap_hash: str
    storyboard_md5: Optional[str]
    iv_b64: bytes
    unique_ids: str
    score_time: int
    osu_version: str
    client_hash_b64: bytes
    replay_data: bytes
    score_id: int
