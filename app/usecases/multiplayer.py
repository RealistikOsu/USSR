from __future__ import annotations

import logging
from dataclasses import dataclass

import app.state.services
from app.adapters import bancho_service
from app.utils.score_utils import calculate_accuracy


@dataclass
class MatchDetails:
    match_name: str
    match_id: int
    slot_id: int
    game_id: int
    team: int


async def get_player_match_details(user_id: int) -> MatchDetails | None:
    match_status = await bancho_service.get_player_match_details(user_id)
    if match_status is None:
        return None

    return MatchDetails(
        match_name=match_status.match_name,
        match_id=match_status.match_id,
        slot_id=match_status.slot_id,
        game_id=match_status.game_id,
        team=match_status.team,
    )


async def insert_match_game_score(
    match_id: int,
    game_id: int,
    user_id: int,
    mode: int,
    count_300: int,
    count_100: int,
    count_50: int,
    count_miss: int,
    count_geki: int,
    count_katu: int,
    score: int,
    max_combo: int,
    mods: int,
    passed: bool,
    team: int,
) -> None:
    accuracy = calculate_accuracy(
        n300=count_300,
        n100=count_100,
        n50=count_50,
        ngeki=count_geki,
        nkatu=count_katu,
        nmiss=count_miss,
        vanilla_mode=mode,
    )
    query = """
    INSERT INTO match_game_scores
        (id, match_id, game_id, user_id, mode, count_300, count_100, count_50, count_miss,
         count_geki, count_katu, score, accuracy, max_combo, mods, passed, team, timestamp)
    VALUES
        (NULL, :match_id, :game_id, :user_id, :mode, :count_300, :count_100, :count_50, :count_miss,
         :count_geki, :count_katu, :score, :accuracy, :max_combo, :mods, :passed, :team, NOW())
    """
    params = {
        "match_id": match_id,
        "game_id": game_id,
        "user_id": user_id,
        "mode": mode,
        "count_300": count_300,
        "count_100": count_100,
        "count_50": count_50,
        "count_miss": count_miss,
        "count_geki": count_geki,
        "count_katu": count_katu,
        "score": score,
        "accuracy": accuracy,
        "max_combo": max_combo,
        "mods": mods,
        "passed": passed,
        "team": team,
    }
    try:
        await app.state.services.database.execute(query, params)
    except Exception:
        logging.exception("Failed to insert match game score", extra=params)
