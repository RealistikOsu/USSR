from __future__ import annotations

import asyncio
import random
import time
from typing import Any
from typing import Optional

import app.state
from app.constants.mode import Mode
from app.constants.ranked_status import RankedStatus
from app.models.beatmap import Beatmap
from config import config

MD5_CACHE: dict[str, Beatmap] = {}
ID_CACHE: dict[int, Beatmap] = {}
SET_CACHE: dict[int, list[Beatmap]] = {}


async def update_beatmap(beatmap: Beatmap) -> Optional[Beatmap]:
    if not beatmap.deserves_update:
        return beatmap

    new_beatmap = await id_from_api(beatmap.id)
    if new_beatmap:
        # handle deleting the old beatmap etc.

        if new_beatmap.md5 != beatmap.md5:
            # delete any instances of the old map
            MD5_CACHE.pop(beatmap.md5, None)

            asyncio.create_task(
                app.state.services.database.execute(
                    "DELETE FROM beatmaps WHERE beatmap_md5 = :old_md5",
                    {"old_md5": beatmap.md5},
                ),
            )

            if beatmap.frozen:
                # if the previous version is status frozen, we should force the old status on the new version
                new_beatmap.status = beatmap.status
    else:
        # it's now unsubmitted!
        asyncio.create_task(
            app.state.services.database.execute(
                "DELETE FROM beatmaps WHERE beatmap_md5 = :old_md5",
                {"old_md5": beatmap.md5},
            ),
        )

        return None

    # update for new shit
    new_beatmap.last_update = int(time.time())

    asyncio.create_task(save(new_beatmap))  # i don't trust mysql for some reason
    MD5_CACHE[new_beatmap.md5] = new_beatmap
    ID_CACHE[new_beatmap.id] = new_beatmap

    return new_beatmap


async def fetch_by_md5(md5: str) -> Optional[Beatmap]:
    if beatmap := md5_from_cache(md5):
        return beatmap

    if beatmap := await md5_from_database(md5):
        MD5_CACHE[md5] = beatmap
        ID_CACHE[beatmap.id] = beatmap

        return beatmap

    if beatmap := await md5_from_api(md5):
        MD5_CACHE[md5] = beatmap
        ID_CACHE[beatmap.id] = beatmap

        return beatmap


async def fetch_by_id(id: int) -> Optional[Beatmap]:
    if beatmap := id_from_cache(id):
        return beatmap

    if beatmap := await id_from_database(id):
        MD5_CACHE[beatmap.md5] = beatmap
        ID_CACHE[beatmap.id] = beatmap

        return beatmap

    if beatmap := await id_from_api(id):
        MD5_CACHE[beatmap.md5] = beatmap
        ID_CACHE[beatmap.id] = beatmap

        return beatmap


async def fetch_by_set_id(set_id: int) -> Optional[list[Beatmap]]:
    if beatmaps := set_from_cache(set_id):
        return beatmaps

    if beatmaps := await set_from_database(set_id):
        for beatmap in beatmaps:
            MD5_CACHE[beatmap.md5] = beatmap
            ID_CACHE[beatmap.id] = beatmap

            add_to_set_cache(beatmap)

        return beatmaps

    if beatmaps := await set_from_api(set_id):
        for beatmap in beatmaps:
            MD5_CACHE[beatmap.md5] = beatmap
            ID_CACHE[beatmap.id] = beatmap

            add_to_set_cache(beatmap)

        return beatmaps


def add_to_set_cache(beatmap: Beatmap) -> None:
    if set_list := SET_CACHE.get(beatmap.set_id):
        for _map in set_list:
            if _map.id == beatmap.id or _map.md5 == beatmap.md5:
                set_list.remove(_map)

        set_list.append(beatmap)
    else:
        SET_CACHE[beatmap.set_id] = [beatmap]


def set_from_cache(set_id: int) -> Optional[list[Beatmap]]:
    return SET_CACHE.get(set_id)


def md5_from_cache(md5: str) -> Optional[Beatmap]:
    return MD5_CACHE.get(md5)


def id_from_cache(id: int) -> Optional[Beatmap]:
    return ID_CACHE.get(id)


async def md5_from_database(md5: str) -> Optional[Beatmap]:
    db_result = await app.state.services.database.fetch_one(
        "SELECT * FROM beatmaps WHERE beatmap_md5 = :md5",
        {"md5": md5},
    )

    if not db_result:
        return None

    return Beatmap.from_dict(db_result)


async def id_from_database(id: int) -> Optional[Beatmap]:
    db_result = await app.state.services.database.fetch_one(
        "SELECT * FROM beatmaps WHERE beatmap_id = :id",
        {"id": id},
    )

    if not db_result:
        return None

    return Beatmap.from_dict(db_result)


async def set_from_database(set_id: int) -> Optional[list[Beatmap]]:
    db_results = await app.state.services.database.fetch_all(
        "SELECT * FROM beatmaps WHERE beatmapset_id = :id",
        {"id": set_id},
    )

    if not db_results:
        return None

    return [Beatmap.from_dict(db_result) for db_result in db_results]


async def save(beatmap: Beatmap) -> None:
    await app.state.services.database.execute(
        (
            "REPLACE INTO beatmaps (beatmap_id, beatmapset_id, beatmap_md5, song_name, ar, od, mode, rating, "
            "difficulty_std, difficulty_taiko, difficulty_ctb, difficulty_mania, max_combo, hit_length, bpm, playcount, "
            "passcount, ranked, latest_update, ranked_status_freezed, file_name) VALUES (:beatmap_id, :beatmapset_id, :beatmap_md5, :song_name, "
            ":ar, :od, :mode, :rating, :difficulty_std, :difficulty_taiko, :difficulty_ctb, :difficulty_mania, :max_combo, :hit_length, :bpm, "
            ":playcount, :passcount, :ranked, :latest_update, :ranked_status_freezed, :file_name)"
        ),
        beatmap.db_dict,
    )


GET_BEATMAP_URL = "https://old.ppy.sh/api/get_beatmaps"
GET_BEATMAP_FALLBACK_URL = config.api_fallback_url + "/get_beatmaps"


async def _make_get_beatmaps_request(args: dict[str, Any]) -> Optional[list[Beatmap]]:
    url = GET_BEATMAP_FALLBACK_URL
    if config.api_keys_pool:
        url = GET_BEATMAP_URL
        args["k"] = random.choice(config.api_keys_pool)

    async with app.state.services.http.get(
        url,
        params=args,
    ) as response:
        if not response or response.status != 200:
            return None

        response_json = await response.json()
        if not response_json:
            return None

    return parse_from_osu_api(response_json)


async def md5_from_api(md5: str) -> Optional[Beatmap]:
    beatmaps = await _make_get_beatmaps_request(
        {"h": md5},
    )

    if beatmaps is None:
        return None

    for beatmap in beatmaps:
        asyncio.create_task(save(beatmap))
        add_to_set_cache(beatmap)

    for beatmap in beatmaps:
        if beatmap.md5 == md5:
            return beatmap


async def id_from_api(id: int, should_save: bool = True) -> Optional[Beatmap]:
    beatmaps = await _make_get_beatmaps_request(
        {"b": id},
    )

    if beatmaps is None:
        return None

    if should_save:
        for beatmap in beatmaps:
            asyncio.create_task(save(beatmap))
            add_to_set_cache(beatmap)

    for beatmap in beatmaps:
        if beatmap.id == id:
            return beatmap


async def set_from_api(id: int) -> Optional[list[Beatmap]]:
    beatmaps = await _make_get_beatmaps_request(
        {"s": id},
    )

    if beatmaps is None:
        return None

    for beatmap in beatmaps:
        asyncio.create_task(save(beatmap))
        add_to_set_cache(beatmap)

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

        filename = ("{artist} - {title} ({creator}) [{version}].osu").format(
            **response_json,
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
                difficulty_std=0.0,
                difficulty_taiko=0.0,
                difficulty_ctb=0.0,
                difficulty_mania=0.0,
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


async def increment_playcount(beatmap: Beatmap, passcount: bool = True) -> None:
    beatmap.plays += 1
    if passcount:
        beatmap.passes += 1

    await app.state.services.database.execute(
        "UPDATE beatmaps SET passcount = :pass, playcount = :play WHERE beatmap_md5 = :md5",
        {"play": beatmap.plays, "pass": beatmap.passes, "md5": beatmap.md5},
    )
