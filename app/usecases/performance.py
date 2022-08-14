from __future__ import annotations

import hashlib
import math
import os

from rosu_pp_py import Calculator
from rosu_pp_py import ScoreParams

import app.state
import logging
from app.constants.mode import Mode
from app.models.score import Score
from app.objects.oppai import OppaiWrapper
from app.objects.path import Path

OPPAI_DIR = Path.cwd() / "akatsuki-pp"
OPPAI_LIB = OPPAI_DIR / "liboppai.so"


def ensure_oppai() -> None:
    if not OPPAI_DIR.exists():
        logging.error(f"Oppai folder {OPPAI_DIR} does not exist!")
        raise RuntimeError

    if not OPPAI_LIB.exists():
        logging.warning(f"Oppai ({OPPAI_DIR}) not built, building...")
        os.system(f"cd {OPPAI_DIR} && chmod +x libbuild && ./libbuild && cd ..")


async def check_local_file(osu_file_path: Path, map_id: int, map_md5: str) -> bool:
    if (
        not osu_file_path.exists()
        or hashlib.md5(osu_file_path.read_bytes()).hexdigest() != map_md5
    ):
        async with app.state.services.http.get(
            f"https://old.ppy.sh/osu/{map_id}",
        ) as response:
            if response.status != 200:
                return False

            osu_file_path.write_bytes(await response.read())

    return True


def calculate_oppai(
    mode: Mode,
    mods: int,
    max_combo: int,
    acc: float,
    nmiss: int,
    osu_file_path: Path,
) -> tuple[float, float]:
    with OppaiWrapper(str(OPPAI_LIB)) as ezpp:
        ezpp.configure(
            mode=mode.as_vn,
            acc=acc,
            mods=mods,
            combo=max_combo,
            nmiss=nmiss,
        )
        ezpp.calculate(osu_file_path)

        pp = ezpp.get_pp()
        sr = ezpp.get_sr()

        for _attr in (
            pp,
            sr,
        ):
            if math.isinf(_attr) or math.isnan(_attr):
                return (0.0, 0.0)

        return (round(pp, 2), round(sr, 2))

    return 0.0, 0.0


def calculate_rosu(
    mode: Mode,
    mods: int,
    max_combo: int,
    score: int,
    acc: float,
    nmiss: int,
    osu_file_path: Path,
) -> tuple[float, float]:
    try:
        calculator = Calculator(str(osu_file_path))
    except Exception as e:
        # messed up .osu file
        if "osu file format" in str(e):
            return (0.0, 0.0)

        raise e

    params = ScoreParams(
        mode=mode.as_vn,
        mods=mods,
        combo=max_combo,
        score=score,
        acc=acc,
        nMisses=nmiss,
    )

    (res,) = calculator.calculate(params)

    for _attr in (
        res.pp,
        res.stars,
    ):
        if math.isinf(_attr) or math.isnan(_attr):
            return (0.0, 0.0)

    return (round(res.pp, 2), round(res.stars, 2))


# TODO: split sr & pp calculations
def calculate_performance(
    mode: Mode,
    mods: int,
    max_combo: int,
    score: int,
    acc: float,
    nmiss: int,
    osu_file_path: Path,
) -> tuple[float, float]:
    if (mode.relax or mode.autopilot) and mode.as_vn == 0:
        return calculate_oppai(mode, mods, max_combo, acc, nmiss, osu_file_path)
    else:
        return calculate_rosu(mode, mods, max_combo, score, acc, nmiss, osu_file_path)


def calculate_score(score: Score, osu_file_path: Path) -> None:
    score.pp, score.sr = calculate_performance(
        score.mode,
        score.mods.value,
        score.max_combo,
        score.score,
        score.acc,
        score.nmiss,
        osu_file_path,
    )
