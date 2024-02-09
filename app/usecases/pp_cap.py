from __future__ import annotations

import logging
from typing import NamedTuple

import app.state
from app.constants.mode import Mode


class CapValue(NamedTuple):
    pp: int
    flashlight_pp: int

async def get_pp_cap(mode: Mode, flashlight: bool) -> int:
    pp_cap = await fetch(mode)
    assert pp_cap is not None

    if flashlight:
        return pp_cap.flashlight_pp

    return pp_cap.pp


async def fetch(mode: Mode) -> CapValue:
    pp_cap = await app.state.services.database.fetch_one(
        f"SELECT pp, flashlight_pp FROM pp_limits WHERE mode = :mode and relax = :relax",
        {"mode": mode.as_vn, "relax": mode.relax},
    )

    if not pp_cap:
        return CapValue(0, 0)

    return CapValue(pp_cap["pp"], pp_cap["flashlight_pp"])
