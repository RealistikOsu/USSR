from __future__ import annotations

import asyncio
import logging
from typing import NamedTuple

import app.state
from app.constants.mode import Mode
from app.constants.mods import Mods


class CapKey(NamedTuple):
    mode: Mode

class CapValue(NamedTuple):
    pp: int
    flashlight_pp: int

PP_CAPS: dict[CapKey, CapValue] = {}
FIVE_MINUTES = 60 * 5


async def get_pp_cap(mode: Mode, flashlight: bool) -> int:
    cap_key = CapKey(mode)

    pp_cap = PP_CAPS.get(cap_key)
    if pp_cap is None:
        pp_cap = await update_pp_cap(mode)
        
    assert pp_cap is not None
    
    if flashlight:
        return pp_cap.flashlight_pp
    
    return pp_cap.pp


async def update_pp_cap(mode: Mode) -> CapValue:
    cap_key = CapKey(mode)

    pp_cap = await app.state.services.database.fetch_val(
        f"SELECT pp, flashlight_pp FROM pp_limits WHERE mode = :mode and relax = :relax",
        {"mode": mode.as_vn, "relax": mode.relax},
    )

    if not pp_cap:
        PP_CAPS[cap_key] = CapValue(0, 0)
        return CapValue(0, 0)

    PP_CAPS[cap_key] = CapValue(pp_cap["pp"], pp_cap["flashlight_pp"])
    return pp_cap


async def load_pp_caps() -> None:
    for mode in Mode:
        await update_pp_cap(mode)

    logging.info(f"Cached pp caps!")


async def update_pp_cap_task() -> None:
    while True:
        await load_pp_caps()
        await asyncio.sleep(FIVE_MINUTES)
