# Anticheat related helper functions.
from config import conf
from consts.c_modes import CustomModes
from typing import TYPE_CHECKING
from globs.conn import sql

if TYPE_CHECKING:
    from objects.score import Score

_caps = {
    CustomModes.VANILLA: conf.pp_cap_vn,
    CustomModes.RELAX: conf.pp_cap_rx,
    CustomModes.AUTOPILOT: conf.pp_cap_ap,
}

def get_pp_cap(mode: CustomModes) -> int:
    return _caps[mode]

async def surpassed_cap_restrict(score: 'Score') -> bool:
    """Checks if the user surpassed the PP cap for their mode and should
    be restricted."""

    res = score.pp > get_pp_cap(score.mode)
    if res:
        # TODO: Maybe cache it?
        is_verified = await sql.fetchcol(
            "SELECT 1 FROM user_badges WHERE user = %s AND "
            f"badge = {conf.srv_ver_badge_id} LIMIT 1",
            (score.user_id,)
        )
        res = not is_verified
    return res
