# The screenshot related handlers.
from helpers.user import safe_name
from libs.crypt import gen_rand_str
from aiopath import AsyncPath as Path
from globals.caches import check_auth, name
from helpers.pep import check_online
from globals.connections import redis
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse
from logger import error, info
from config import config
import os

SS_DELAY = 10 # Seconds per screenshot.
FS_LIMIT = 500_000 # Rosu screenshots don't exceed this.
ERR_RESP = "https://c.ussr.pl/" # We do a lil trolley.
SS_NAME_LEN = 8

if config.DATA_DIR[0] == "/" or config.DATA_DIR[1] == ":":
    SS_PATH = Path(config.DATA_DIR) / "screenshots"
else:
    SS_PATH = os.getcwd() / Path(config.DATA_DIR) / "screenshots"


async def is_ratelimit(ip: str) -> bool:
    """Checks if an IP is ratelimited from taking screenshots. If not,
    it establises the limit in Redis."""

    rl_key = "ussr:ss_limit:" + ip
    if await redis.get(rl_key): return True
    await redis.set(rl_key, 1, expire= SS_DELAY)
    return False

async def upload_image_handler(req: Request) -> Response:
    """Handles screenshot uploads (POST /web/osu-screenshot.php)."""

    post_args = await req.form()

    username = post_args["u"]
    password = post_args["p"]
    if not await check_auth(username, password):
        return PlainTextResponse("no")
    
    # This is a particularly dangerous endpoint.
    user_id = await name.id_from_safe(safe_name(username))
    if not await check_online(user_id):
        error(f"User {username} ({user_id}) tried to upload a screenshot while offline.")
        return PlainTextResponse(ERR_RESP)
    
    if req.headers.get("user-agent") != "osu!":
        error(f"User {username} ({user_id}) tried to upload a screenshot using a bot.")
        return PlainTextResponse(ERR_RESP)

    # LETS style ratelimit.
    if await is_ratelimit(req.headers["x-real-ip"]):
        error(f"User {username} ({user_id}) tried to upload a screenshot while ratelimited.")
        return PlainTextResponse(ERR_RESP)

    content = await post_args["ss"].read()

    if content.__sizeof__() > FS_LIMIT:
        return PlainTextResponse(ERR_RESP)

    if content[6:10] in (b'JFIF', b'Exif'):
        ext =  'jpeg'
    elif content.startswith(b'\211PNG\r\n\032\n'):
        ext = 'png'
    else:
        error(f"User {username} ({user_id}) tried to upload unknown extention file.")
        return PlainTextResponse(ERR_RESP)

    # Get a random name for the file that does not overlap.
    while True:
        info("Generating a new screenshot name...")
        path = SS_PATH / (f_name := f"{gen_rand_str(SS_NAME_LEN)}.{ext}")
        if not await path.exists():
            break

    # Write file.
    await path.write_bytes(content)

    info(f"User {username} ({user_id}) has uploaded the screenshot {f_name}")
    return PlainTextResponse(f_name)