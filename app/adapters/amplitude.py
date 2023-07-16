from __future__ import annotations

import time
from typing import Any
from typing import Mapping

from tenacity import retry
from tenacity import stop_after_attempt

import config
from app.state import services


# TODO: better client error & 429 handling
@retry(stop=stop_after_attempt(7))
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

    async with services.http.post(
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
    ) as resp:
        resp.raise_for_status()


@retry(stop=stop_after_attempt(7))
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

    async with services.http.post(
        url="https://api.amplitude.com/identify",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "api_key": config.AMPLITUDE_API_KEY,
            "identification": [amplitude_event],
        },
    ) as resp:
        resp.raise_for_status()
