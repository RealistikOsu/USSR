# Implementation of the ripple api for compatibility purposes.
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from constants.modes import Mode
from constants.c_modes import CustomModes
from constants.mods import Mods
from helpers.beatmap import bmap_md5_from_id
from logger import info
from pp.main import select_calculator
from objects.beatmap import Beatmap

async def status_handler(request: Request) -> Response:
    """Handles the `/api/v1/status` with a constant response."""

    return JSONResponse({
        "status": 200,
        "server_status": 1,
    })

TILLERINO_PERCENTAGES = (
    100, 99, 98, 95
)

# PP Calculation. TODO: Ratelimit.
async def pp_handler(request: Request) -> Response:
    """Handles the `/api/v1/pp` api."""

    beatmap_id = request.query_params.get("b")
    if not beatmap_id: 
        return JSONResponse({
            "status": 400,
            "message": "Missing b GET argument."
        }, 400)

    mods = int(request.query_params.get("m", 0))
    mods = Mods(mods)

    mode = int(request.query_params.get("g", 0))
    mode = Mode(mode)

    acc_str = request.query_params.get("a")
    accuracy = float(acc_str) if acc_str else None
    combo = int(request.query_params.get("max_combo", 0))
    c_mode = CustomModes.from_mods(mods, mode)
    do_tillerino = accuracy is None

    # Get our calculator.
    calc = select_calculator(mode, c_mode)()

    # Get beatmap.
    bmap_md5 = await bmap_md5_from_id(beatmap_id)
    if not bmap_md5: 
        return JSONResponse({
            "status": 400,
            "message": "Invalid/non-existent beatmap id."
        }, 400)

    bmap = await Beatmap.from_md5(bmap_md5)

    star_rating = pp_result = 0.0

    # Configure calculator.
    calc.mods = mods.value
    calc.mode = mode.value
    calc.bmap_id = bmap.id
    calc.combo = combo if combo else bmap.max_combo

    if not do_tillerino:
        calc.acc = accuracy
        pp_result, star_rating = await calc.calculate()
    else:
        pp_result = []
        for accuracy in TILLERINO_PERCENTAGES:
            calc.acc = accuracy
            res = await calc.calculate()
            star_rating = res[1]
            pp_result.append(res[0])
    
    info(f"Handled PP Calculation API Request for {bmap.song_name}!")
    
    # Final Response!
    return JSONResponse({
        "status": 200,
        "message": "ok",
        "song_name": bmap.song_name,
        "pp": pp_result,
        "length": bmap.hit_length,
        "stars": star_rating,
        "ar": bmap.ar,
        "bpm": bmap.bpm,
    })
