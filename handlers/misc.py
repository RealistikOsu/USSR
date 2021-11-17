# Rather small endpoints that don't deserve their own file.
from lenhttp import Request
from globs import caches
from helpers.pep import check_online
from helpers.user import safe_name
from helpers.anticheat import get_flag_explanation, log_lastfm_flag
from consts.anticheat import LastFMFlags
from logger import info


RES = b"-3" # This is returned pretty much always.
ERR_PASS = b"error: pass"
ERR_MISC = b"error: no"
async def lastfm_handler(req: Request) -> bytes:
    """Handles the LastFM osu!anticheat endpoint and handles the appropriate action
    based on the result.
    `/web/lastfm.php`
    """

    # Handle authentication.
    username = req.get_args["us"]
    user_id = await caches.name.id_from_safe(safe_name(username))
    if not username: return ERR_PASS

    if not await caches.check_auth(username, req.get_args["ha"]): return ERR_PASS
    if not await check_online(user_id): return ERR_MISC

    # If the first char of this arg is the char "a", a cheat has been flagged.
    bmap_arg: str = req.get_args["b"]
    if bmap_arg.startswith("a"):
        # Now we check the exact cheats they have been flagged for.
        flags = LastFMFlags(int(bmap_arg.removeprefix("a")))
        expl_str = "\n".join(get_flag_explanation(flags))

        info(f"User {username} ({user_id}) has been flagged with {flags!r}!\n" + expl_str)

        # TODO: Some of these may be frequently false. Look which ones are and autorestrict.
        # For now we just log them.
        await log_lastfm_flag(user_id, flags.value, expl_str)
    
    # Response is the same to get the client to shut up.
    return RES
