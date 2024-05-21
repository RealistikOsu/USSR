from __future__ import annotations

import random
import time
from typing import Optional

import app.state
import config
from app.constants.mode import Mode
from app.constants.ranked_status import RankedStatus
from app.models.beatmap import Beatmap


async def update_beatmap(beatmap: Beatmap) -> Optional[Beatmap]:
    if not beatmap.deserves_update:
        return beatmap

    new_beatmap = await id_from_api(beatmap.id, should_save=False)
    if new_beatmap is None:
        # it's now unsubmitted!

        await app.state.services.database.execute(
            "DELETE FROM beatmaps WHERE beatmap_md5 = :old_md5",
            {"old_md5": beatmap.md5},
        )

        return None

    # handle deleting the old beatmap etc.
    if new_beatmap.md5 != beatmap.md5:
        # delete any instances of the old map
        await app.state.services.database.execute(
            "DELETE FROM beatmaps WHERE beatmap_md5 = :old_md5",
            {"old_md5": beatmap.md5},
        )
    else:
        # the map may have changed in some ways (e.g. ranked status),
        # but we want to make sure to keep our stats, because the map
        # is the same from the player's pov (hit objects, ar/od, etc.)
        new_beatmap.plays = beatmap.plays
        new_beatmap.passes = beatmap.passes
        new_beatmap.rating = beatmap.rating

    if beatmap.frozen:
        # if the previous version is status frozen
        # we should force the old status on the new version
        new_beatmap.status = beatmap.status
        new_beatmap.frozen = True

    new_beatmap.last_update = int(time.time())

    await save(new_beatmap)
    return new_beatmap


async def fetch_by_md5(md5: str) -> Optional[Beatmap]:
    if beatmap := await md5_from_database(md5):
        return beatmap

    if beatmap := await md5_from_api(md5):
        return beatmap


async def fetch_by_id(id: int) -> Optional[Beatmap]:
    if beatmap := await id_from_database(id):
        return beatmap

    if beatmap := await id_from_api(id):
        return beatmap


async def fetch_by_set_id(set_id: int) -> list[Beatmap]:
    if beatmaps := await set_from_database(set_id):
        return beatmaps

    if beatmaps := await set_from_api(set_id):
        return beatmaps

    return []


async def md5_from_database(md5: str) -> Optional[Beatmap]:
    db_result = await app.state.services.database.fetch_one(
        "SELECT * FROM beatmaps WHERE beatmap_md5 = :md5",
        {"md5": md5},
    )

    if not db_result:
        return None

    return Beatmap.from_mapping(db_result)


async def id_from_database(id: int) -> Optional[Beatmap]:
    db_result = await app.state.services.database.fetch_one(
        "SELECT * FROM beatmaps WHERE beatmap_id = :id",
        {"id": id},
    )

    if not db_result:
        return None

    return Beatmap.from_mapping(db_result)


async def set_from_database(set_id: int) -> list[Beatmap]:
    db_results = await app.state.services.database.fetch_all(
        "SELECT * FROM beatmaps WHERE beatmapset_id = :id",
        {"id": set_id},
    )

    return [Beatmap.from_mapping(db_result) for db_result in db_results]  # type: ignore


GET_BEATMAP_URL = "https://old.ppy.sh/api/get_beatmaps"


async def save(beatmap: Beatmap) -> None:
    await app.state.services.database.execute(
        (
            "REPLACE INTO beatmaps (beatmap_id, beatmapset_id, beatmap_md5, song_name, ar, od, mode, rating, "
            "max_combo, hit_length, bpm, playcount, passcount, ranked, latest_update, ranked_status_freezed, "
            "file_name) VALUES (:beatmap_id, :beatmapset_id, :beatmap_md5, :song_name, :ar, :od, :mode, "
            ":rating, :max_combo, :hit_length, :bpm, :playcount, :passcount, :ranked, :latest_update, "
            ":ranked_status_freezed, :file_name)"
        ),
        {
            "beatmap_id": beatmap.id,
            "beatmapset_id": beatmap.set_id,
            "beatmap_md5": beatmap.md5,
            "song_name": beatmap.song_name,
            "ar": beatmap.ar,
            "od": beatmap.od,
            "mode": beatmap.mode.value,
            "rating": beatmap.rating,
            "max_combo": beatmap.max_combo,
            "hit_length": beatmap.hit_length,
            "bpm": beatmap.bpm,
            "playcount": beatmap.plays,
            "passcount": beatmap.passes,
            "ranked": beatmap.status.value,
            "latest_update": beatmap.last_update,
            "ranked_status_freezed": beatmap.frozen,
            "file_name": beatmap.filename,
        },
    )


async def md5_from_api(md5: str, should_save: bool = True) -> Optional[Beatmap]:
    api_key = random.choice(config.API_KEYS_POOL)

    response = await app.state.services.http_client.get(
        GET_BEATMAP_URL,
        params={"k": api_key, "h": md5},
    )
    if response.status_code == 404:
        return None

    response.raise_for_status()

    response_json = response.json()
    if not response_json:
        return None

    beatmaps = parse_from_osu_api(response_json)

    if should_save:
        for beatmap in beatmaps:
            await save(beatmap)

    for beatmap in beatmaps:
        if beatmap.md5 == md5:
            return beatmap


async def id_from_api(id: int, should_save: bool = True) -> Optional[Beatmap]:
    api_key = random.choice(config.API_KEYS_POOL)

    response = await app.state.services.http_client.get(
        GET_BEATMAP_URL,
        params={"k": api_key, "b": id},
    )
    if response.status_code == 404:
        return None

    response.raise_for_status()

    response_json = response.json()
    if not response_json:
        return None

    beatmaps = parse_from_osu_api(response_json)

    if should_save:
        for beatmap in beatmaps:
            await save(beatmap)

    for beatmap in beatmaps:
        if beatmap.id == id:
            return beatmap


async def set_from_api(id: int, should_save: bool = True) -> Optional[list[Beatmap]]:
    api_key = random.choice(config.API_KEYS_POOL)

    response = await app.state.services.http_client.get(
        GET_BEATMAP_URL,
        params={"k": api_key, "s": id},
    )
    if response.status_code == 404:
        return None

    response.raise_for_status()

    response_json = response.json()
    if not response_json:
        return None

    beatmaps = parse_from_osu_api(response_json)

    if should_save:
        for beatmap in beatmaps:
            await save(beatmap)

    return beatmaps


IGNORED_BEATMAP_CHARS = dict.fromkeys(map(ord, r':\/*<>?"|'), None)

FROZEN_STATUSES = (RankedStatus.RANKED, RankedStatus.APPROVED, RankedStatus.LOVED)


def parse_from_osu_api(
    response_json_list: list[dict],
    frozen: bool = False,
) -> list[Beatmap]:
    maps = []

    for response_json in response_json_list:
        md5 = response_json["file_md5"]
        id = int(response_json["beatmap_id"])
        set_id = int(response_json["beatmapset_id"])

        filename = (
            ("{artist} - {title} ({creator}) [{version}].osu")
            .format(**response_json)
            .translate(IGNORED_BEATMAP_CHARS)
        )

        song_name = (
            ("{artist} - {title} [{version}]")
            .format(**response_json)
            .translate(IGNORED_BEATMAP_CHARS)
        )

        hit_length = int(response_json["hit_length"])

        if _max_combo := response_json.get("max_combo"):
            max_combo = int(_max_combo)
        else:
            max_combo = 0

        ranked_status = RankedStatus.from_osu_api(int(response_json["approved"]))
        if ranked_status in FROZEN_STATUSES:
            frozen = True  # beatmaps are always frozen when ranked/approved/loved

        mode = Mode(int(response_json["mode"]))

        if _bpm := response_json.get("bpm"):
            bpm = round(float(_bpm))
        else:
            bpm = 0

        od = float(response_json["diff_overall"])
        ar = float(response_json["diff_approach"])

        maps.append(
            Beatmap(
                md5=md5,
                id=id,
                set_id=set_id,
                song_name=song_name,
                status=ranked_status,
                plays=0,
                passes=0,
                mode=mode,
                od=od,
                ar=ar,
                hit_length=hit_length,
                last_update=int(time.time()),
                max_combo=max_combo,
                bpm=bpm,
                filename=filename,
                frozen=frozen,
                rating=10.0,
            ),
        )

    return maps


async def increment_playcount(
    *,
    beatmap: Beatmap,
    increment_passcount: bool,
) -> None:
    beatmap.plays += 1
    if increment_passcount:
        beatmap.passes += 1

    await app.state.services.database.execute(
        "UPDATE beatmaps SET passcount = passcount + :passcount_increment, playcount = playcount + 1 WHERE beatmap_md5 = :md5",
        {"passcount_increment": int(increment_passcount), "md5": beatmap.md5},
    )
