from __future__ import annotations

import app.state
from app.constants.mode import Mode

# 0 = none
# 1 = vanilla
# 2 = relax
# 2 = autopilot
# 3 = all


def _match_verified(whitelist_int: int, mode: Mode) -> bool:
    if mode.autopilot:
        return whitelist_int & 2 != 0  # TODO: make this 4
    elif mode.relax:
        return whitelist_int & 2 != 0
    else:
        return whitelist_int & 1 != 0


async def get_whitelisted(user_id: int, mode: Mode) -> bool:
    whitelist_int = await app.state.services.database.fetch_val(
        "SELECT whitelist FROM users WHERE id = :uid",
        {"uid": user_id},
    )
    return _match_verified(whitelist_int, mode)
