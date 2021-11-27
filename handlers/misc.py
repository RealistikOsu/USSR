# Rather small endpoints that don't deserve their own file.
from functools import cache
from lenhttp import Request
from globs import caches
from globs.conn import sql
from helpers.pep import check_online
from helpers.user import (
    log_user_error,
    safe_name,
    get_friends,
    update_last_active,
    fetch_user_country,
)
from helpers.anticheat import get_flag_explanation, log_lastfm_flag
from helpers.beatmap import user_rated_bmap, add_bmap_rating
from consts.anticheat import LastFMFlags
from logger import info
from objects.beatmap import Beatmap


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

async def getfriends_handler(req: Request) -> str:
    """Gives the client all of the user IDs of friends.
    Handles `/web/osu-getfriends.php`
    """

    username = req.get_args["u"]
    user_id = await caches.name.id_from_safe(safe_name(username))
    if not username: return ERR_PASS
    if not await caches.check_auth(username, req.get_args["h"]): return ERR_PASS

    friend_id = await get_friends(user_id)
    info(f"Served friends list to {username} ({user_id})")
    return "\n".join(map(str, friend_id))

async def osu_error_handler(req: Request) -> bytes:
    """The endpoint to which the client reports any errors that the client
    encounters. Implementing it for potential anticheat use later on.
    DONT TAKE THE DATA FROM THIS ENDPOINT AS COMPLETE TRUTH.
    Handles `/web/osu-error.php`
    """

    # Do not take anonymous logs as they are rather useless to us.
    if not (user_id := req.post_args.get("i")): return b""
    user_id = int(user_id)
    username = req.post_args["u"]

    info(f"{username} ({user_id}) has experienced a client exception! Logging to the database.")

    await log_user_error(user_id, req.post_args["traceback"], req.post_args["config"],
                         req.post_args["version"], req.post_args["exehash"])

    # TODO: Scan config for malicious entries (maybe cheat client config options) and password auth.
    return b""

async def beatmap_rate_handler(req: Request) -> str:
    """Handles the beatmap rating procedure.
    Handles `/web/osu-rate.php`
    """

    bmap_md5 = req.get_args["c"]
    username = req.get_args["u"]
    password = req.get_args["p"]
    rating   = req.get_args.get("v") # Optional

    # Handle user authentication.
    user_id = await caches.name.id_from_safe(safe_name(username))
    if not await caches.password.check_password(user_id, password): return ERR_PASS

    bmap = await Beatmap.from_md5(bmap_md5)
    if not bmap or not bmap.has_leaderboard: return "not ranked"

    if await user_rated_bmap(user_id, bmap_md5): return f"alreadyvoted\n{bmap.rating}"
    
    # They are casting a new vote.
    if rating:
        rating = int(rating)
        # Check if vote is within the 1-10 range to stop exploits.
        if not 1 <= rating <= 10: return ERR_MISC

        # Add the vote to the database and recalculate the rating.
        new_rating = await add_bmap_rating(user_id, bmap_md5, rating)
        bmap.rating = new_rating
        
        info(f"User {username} ({user_id}) has rated {bmap.song_name} with {rating} "
             f"stars (current average {new_rating}).")
        return f"{new_rating:.2f}"
    
    return "ok"

async def get_seasonals_handler(req: Request):
    """Handles `/web/osu-getseasonal.php`, returning a JSON list of seasonal
    images links."""

    info("Serving seasonal backgrounds!")
    seasonal_db = await sql.fetchall(
        "SELECT url FROM seasonal_bg WHERE enabled = 1"
    )

    return req.return_json(
        200,
        [s[0] for s in seasonal_db]
    )

async def bancho_connect(req: Request) -> str:
    """Handles `/web/bancho_connect.php` as a basic form of login."""

    # TODO: Be able to detect when the bancho is down and make sure the user
    # is treated as online during online checks. Right now i just use this to
    # update the last_active for the user.
    username = req.get_args["u"]
    password = req.get_args["h"]
    user_id = caches.name.id_from_safe(safe_name(username))

    if not await caches.password.check_password(user_id, password):
        return "error: pass"
    
    # TODO: Maybe some cache refreshes?
    info(f"{username} ({user_id}) has logged in!")
    update_last_active(user_id)

    # Endpoint responds with the country of the user for cases where
    # bancho is offline and it cannot fetch it from there.
    return await fetch_user_country(user_id)
