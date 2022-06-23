from __future__ import annotations

from app.constants.mode import Mode
from typing import NamedTuple
import asyncio
from app.constants.mods import Mods
import app.state
import logger


class CapKey(NamedTuple):
    mode: Mode
    mods: Mods


PP_CAPS: dict[CapKey, int] = {}
FIVE_MINUTES = 60 * 5


async def get_pp_cap(mode: Mode, mods: Mods) -> int:
    cap_key = CapKey(mode, mods)

    if pp_cap := PP_CAPS.get(cap_key):
        return pp_cap

    return await update_pp_cap(mode, mods)


async def update_pp_cap(mode: Mode, mods: Mods) -> int:
    cap_key = CapKey(mode, mods)

    prefix = ""
    if mode.relax:
        prefix += "relax_"
    elif mode.autopilot:
        prefix += "autopilot_"

    if mods & Mods.FLASHLIGHT:
        prefix += "flashlight_"

    pp_cap = await app.state.services.database.fetch_val(
        f"SELECT {prefix}pp FROM pp_limits WHERE gamemode = :mode",
        {"mode": mode.as_vn},
    )

    if not pp_cap:
        PP_CAPS[cap_key] = 0
        return 0  # xd

    PP_CAPS[cap_key] = pp_cap
    return pp_cap


async def load_pp_caps() -> None:
    for mode, mods in (
        # std
        (Mode.STD, Mods.NOMOD),
        (Mods.STD, Mods.FLASHLIGHT),
        (Mode.STD_RX, Mods.NOMOD),
        (Mode.STD_RX, Mods.FLASHLIGHT),
        (Mode.STD_AP, Mods.NOMOD),
        (Mode.STD_AP, Mods.FLASHLIGHT)
        # taiko
        (Mode.TAIKO, Mods.NOMOD),
        (Mods.TAIKO, Mods.FLASHLIGHT),
        (Mode.TAIKO_RX, Mods.NOMOD),
        (Mode.TAIKO_RX, Mods.FLASHLIGHT),
        # catch
        (Mode.CATCH, Mods.NOMOD),
        (Mods.CATCH, Mods.FLASHLIGHT),
        (Mode.CATCH_RX, Mods.NOMOD),
        (Mode.CATCH_RX, Mods.FLASHLIGHT),
        # mania
        (Mode.MANIA, Mods.NOMOD),
        (Mode.MANIA, Mods.FLASHLIGHT),
    ):
        await update_pp_cap(mode, mods)

    logger.info(f"Cached pp caps!")


async def update_pp_cap_task() -> None:
    while True:
        await load_pp_caps()
        await asyncio.sleep(FIVE_MINUTES)
