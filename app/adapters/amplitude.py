from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from typing import TYPE_CHECKING

from tenacity import retry
from tenacity import wait_exponential
from tenacity.stop import stop_after_attempt

import config
from app.reliability import retry_if_exception_network_related
from app.state import services

if TYPE_CHECKING:
    from app.models.achievement import Achievement
    from app.models.beatmap import Beatmap
    from app.models.score import Score
    from app.models.user import User


def format_mode(mode: int) -> str:
    mode_mapping: dict[int, str] = {
        0: "osu!std",
        1: "osu!taiko",
        2: "osu!catch",
        3: "osu!mania",
        4: "osu!std relax",
        5: "osu!taiko relax",
        6: "osu!catch relax",
        # no mania relax
        8: "osu!std autopilot",
        # no taiko autopilot
        # no catch autopilot
        # no mania autopilot
    }

    return mode_mapping[mode]


def format_user(user: User) -> dict[str, Any]:
    return {
        "user_id": user.id,
        "username": user.name,
        "privileges": user.privileges,
        "country": user.country,
    }


def format_score(score: Score) -> dict[str, Any]:
    return {
        "score_id": score.id,
        "beatmap_md5": score.map_md5,
        "score": score.score,
        "performance": score.pp,
        "accuracy": score.acc,
        "max_combo": score.max_combo,
        "mods": repr(score.mods),
        "game_mode": format_mode(score.mode),
        "passed": score.passed,
        "full_combo": score.full_combo,
        "300_count": score.n300,
        "100_count": score.n100,
        "50_count": score.n50,
        "katus_count": score.nkatu,
        "gekis_count": score.ngeki,
        "misses_count": score.nmiss,
        "time": score.time,
        "play_time": score.time_elapsed,
        "status": score.status.name,
        "checksum": score.online_checksum,
    }


def format_beatmap(beatmap: Beatmap) -> dict[str, Any]:
    return {
        "beatmap_md5": beatmap.md5,
        "beatmap_id": beatmap.id,
        "beatmapset_id": beatmap.set_id,
        "song_name": beatmap.song_name,
        "ranked_status": beatmap.status.name,
        "plays": beatmap.plays,
        "passes": beatmap.passes,
        "game_mode": format_mode(beatmap.mode),
        "od": beatmap.od,
        "ar": beatmap.ar,
        # TODO: context-aware difficulty rating
        "awards_performance": beatmap.gives_pp,
        "hit_length": beatmap.hit_length,
        "last_update": beatmap.last_update,
        "max_combo": beatmap.max_combo,
        "bpm": beatmap.bpm,
        "file_name": beatmap.filename,
        "frozen": beatmap.frozen,
        "rating": beatmap.rating,
    }


def format_achievement(achievement: Achievement) -> dict[str, Any]:
    return {
        "achievement_id": achievement.id,
        "file_name": achievement.file,
        "name": achievement.name,
        "description": achievement.desc,
    }


@retry(
    retry=retry_if_exception_network_related(),
    wait=wait_exponential(),
    stop=stop_after_attempt(10),
    reraise=True,
)
async def track(
    event_name: str,
    user_id: str | None = None,
    device_id: str | None = None,
    time: int | None = None,
    event_properties: Mapping[str, Any] | None = None,
    user_properties: Mapping[str, Any] | None = None,
    groups: Mapping[str, Any] | None = None,
    app_version: str | None = None,
    platform: str | None = None,
    os_name: str | None = None,
    os_version: str | None = None,
    device_brand: str | None = None,
    device_manufacturer: str | None = None,
    device_model: str | None = None,
    carrier: str | None = None,
    country: str | None = None,
    region: str | None = None,
    city: str | None = None,
    dma: str | None = None,
    language: str | None = None,
    price: float | None = None,
    quantity: int | None = None,
    revenue: float | None = None,
    product_id: str | None = None,
    revenue_type: str | None = None,
    location_lat: float | None = None,
    location_lng: float | None = None,
    ip: str | None = None,
    idfa: str | None = None,
    idfv: str | None = None,
    adid: str | None = None,
    android_id: str | None = None,
    event_id: int | None = None,
    session_id: int | None = None,
    insert_id: str | None = None,
    # plan: AmplitudeTrackingPlan | None = None,
) -> None:
    assert user_id or device_id, "user_id or device_id must be provided"
    if event_properties is None:
        event_properties = {}
    if user_properties is None:
        user_properties = {}

    amplitude_event = {
        "user_id": user_id,
        "device_id": device_id,
        "event_type": event_name,
        "time": time,
        "event_properties": event_properties,
        "user_properties": user_properties,
        "groups": groups,
        "app_version": app_version,
        "platform": platform,
        "os_name": os_name,
        "os_version": os_version,
        "device_brand": device_brand,
        "device_manufacturer": device_manufacturer,
        "device_model": device_model,
        "carrier": carrier,
        "country": country,
        "region": region,
        "city": city,
        "dma": dma,
        "language": language,
        "price": price,
        "quantity": quantity,
        "revenue": revenue,
        "product_id": product_id,
        "revenue_type": revenue_type,
        "location_lat": location_lat,
        "location_lng": location_lng,
        "ip": ip,
        "idfa": idfa,
        "idfv": idfv,
        "adid": adid,
        "android_id": android_id,
        "event_id": event_id,
        "session_id": session_id,
        "insert_id": insert_id,
    }

    amplitude_event = {k: v for k, v in amplitude_event.items() if v is not None}

    response = await services.http_client.post(
        url="https://api.amplitude.com/2/httpapi",
        headers={"Content-Type": "application/json"},
        json={
            "api_key": config.AMPLITUDE_API_KEY,
            "options": {
                # (akatsuki's user ids start from 1000)
                "min_id_length": 4,
            },
            "events": [amplitude_event],
        },
        timeout=10,
    )
    response.raise_for_status()


@retry(
    retry=retry_if_exception_network_related(),
    wait=wait_exponential(),
    stop=stop_after_attempt(10),
    reraise=True,
)
async def identify(
    user_id: str | None = None,
    device_id: str | None = None,
    user_properties: Mapping[str, Any] | None = None,
    groups: Mapping[str, Any] | None = None,
    app_version: str | None = None,
    platform: str | None = None,
    os_name: str | None = None,
    os_version: str | None = None,
    device_brand: str | None = None,
    device_manufacturer: str | None = None,
    device_model: str | None = None,
    carrier: str | None = None,
    country: str | None = None,
    region: str | None = None,
    city: str | None = None,
    dma: str | None = None,
    language: str | None = None,
    paying: str | None = None,
    start_version: str | None = None,
) -> None:
    assert user_id or device_id, "user_id or device_id must be provided"

    amplitude_event = {
        "user_id": user_id,
        "device_id": device_id,
        "user_properties": user_properties,
        "groups": groups,
        "app_version": app_version,
        "platform": platform,
        "os_name": os_name,
        "os_version": os_version,
        "device_brand": device_brand,
        "device_manufacturer": device_manufacturer,
        "device_model": device_model,
        "carrier": carrier,
        "country": country,
        "region": region,
        "city": city,
        "dma": dma,
        "language": language,
        "paying": paying,
        "start_version": start_version,
    }

    amplitude_event = {k: v for k, v in amplitude_event.items() if v is not None}

    response = await services.http_client.post(
        url="https://api.amplitude.com/identify",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "api_key": config.AMPLITUDE_API_KEY,
            "identification": [amplitude_event],
        },
    )
    response.raise_for_status()
