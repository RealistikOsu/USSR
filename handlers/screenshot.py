# The screenshot related handlers.
from libs.crypt import gen_rand_str
from globs.caches import check_auth
from globs.conn import redis
from libs.files import Image
from lenhttp import Request
from logger import error
from config import conf
import traceback
import os

FS_LIMIT = 500000 # Rosu screenshots don't exceed this.
ERR_RESP = "https://c.ussr.pl/" # We do a lil trolley.
SS_DELAY = 30 # Seconds per screenshot.
SS_NAME_LEN = 8
async def upload_image_handler(req: Request) -> str:
    """Handles screenshot uploads (POST /web/osu-screenshot.php)."""

    if not await check_auth(req.post_args["p"], req.post_args["h"]):
        return "no"

    # LETS style ratelimit.
    rl_key = "ussr:ss_limit:" + req.headers["X-Real-IP"] # Use IP.
    if redis.get(rl_key): return ERR_RESP
    await redis.set(rl_key, 1, expire= SS_DELAY)

    # Working with files.
    try:
        im = Image(req.files["ss"])
    except ValueError:
        error(f"Error loading screenshot from user {req.post_args['p']} "
               + traceback.format_exc())
        return ERR_RESP
    
    # Get a random name for the file that does not overlap.
    while not os.path.exists((name := gen_rand_str(SS_NAME_LEN) + "." + im._file_ext)):
        pass

    # Write file.
    im.write(conf.dir_screenshot, name)

    return f"{name}.{im._file_ext}"
