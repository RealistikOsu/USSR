# The screenshot related handlers.
from helpers.user import safe_name
from libs.crypt import gen_rand_str
from globs.caches import check_auth, name
from helpers.pep import check_online
from globs.conn import redis
from libs.files import Image
from lenhttp import Request
from logger import error, info
from config import conf
import traceback
import os

SS_DELAY = 10 # Seconds per screenshot.
async def is_ratelimit(ip: str) -> bool:
    """Checks if an IP is ratelimited from taking screenshots. If not,
    it establises the limit in Redis."""

    rl_key = "ussr:ss_limit:" + ip
    if await redis.get(rl_key): return True
    await redis.set(rl_key, 1, expire= SS_DELAY)
    return False

FS_LIMIT = 500000 # Rosu screenshots don't exceed this.
ERR_RESP = "https://c.ussr.pl/" # We do a lil trolley.
SS_NAME_LEN = 8
async def upload_image_handler(req: Request) -> str:
    """Handles screenshot uploads (POST /web/osu-screenshot.php)."""

    if not await check_auth(req.post_args["u"], req.post_args["p"]):
        return "no"
    
    # This is a particularly dangerous endpoint.
    user_id = await name.id_from_safe(safe_name(req.post_args["u"]))
    if not await check_online(user_id, req.headers["x-real-ip"]):
        return ERR_RESP
    
    if req.headers.get("user-agent") != "osu!": return ERR_RESP

    # LETS style ratelimit.
    if await is_ratelimit(req.headers["x-real-ip"]): return ERR_RESP

    # Working with files.
    try:
        im = Image(req.files["ss"])
    except ValueError:
        error(f"Error loading screenshot from user {req.post_args['u']} "
               + traceback.format_exc())
        return ERR_RESP
    
    # Get a random name for the file that does not overlap.
    while os.path.exists((fname := gen_rand_str(SS_NAME_LEN)) + "." + im._file_ext):
        pass

    # Write file.
    im.write(conf.dir_screenshot, fname)

    info(f"{req.post_args['u']} has uploaded the screenshot {fname}.{im._file_ext}")

    return f"{fname}.{im._file_ext}"
