from __future__ import annotations

import math
import os

from rosu_pp_py import Calculator
from rosu_pp_py import ScoreParams

import logger
from app.models.score import Score
from app.objects.oppai import OppaiWrapper
from app.objects.path import Path

OPPAI_DIRS = (
    "oppai-ap",
    "oppai-rx",
)


def ensure_oppai() -> None:
    for dir in OPPAI_DIRS:
        if not os.path.exists(dir):
            logger.error(f"Oppai folder {dir} does not exist!")
            raise RuntimeError

        if not os.path.exists(f"{dir}/liboppai.so"):
            logger.warning(f"Oppai ({dir}) not built, building...")
            os.system(f"cd {dir} && chmod +x libbuild && ./libbuild && cd ..")


def calculate_oppai(score: Score, osu_file_path: Path) -> tuple[float, float]:
    if score.mode.relax:
        lib_path = "oppai-rx/liboppai.so"
    elif score.mode.relax:
        lib_path = "oppai-ap/liboppai.so"

    with OppaiWrapper(lib_path) as ezpp:
        ezpp.configure(
            mode=score.mode.as_vn,
            acc=score.acc,
            mods=score.mods.value,
            combo=score.max_combo,
            nmiss=score.nmiss,
        )
        ezpp.calculate(str(osu_file_path))

        pp = ezpp.get_pp()
        sr = ezpp.get_sr()

        for _attr in (
            pp,
            sr,
        ):
            if math.isinf(_attr) or math.isnan(_attr):
                return (0.0, 0.0)

        return (round(pp, 2), round(sr, 2))


def calculate_rosu(score: Score, osu_file_path: Path) -> tuple[float, float]:
    calculator = Calculator(str(osu_file_path))
    params = ScoreParams(
        mods=score.mods,
        n50=score.n50,
        n100=score.n100,
        n300=score.n300,
        nKatu=score.nkatu,
        combo=score.max_combo,
        score=score.score,
        acc=score.acc,
        nMisses=score.nmiss,
    )

    (res,) = calculator.calculate(params)

    for _attr in (
        res.pp,
        res.stars,
    ):
        if math.isinf(_attr) or math.isnan(_attr):
            return (0.0, 0.0)

    return (round(res.pp, 2), round(res.stars, 2))


def calculate_score(score: Score, osu_file_path: Path) -> None:
    if (score.mode.relax or score.mode.autopilot) and score.mode.as_vn == 0:
        score.pp, score.sr = calculate_oppai(score, osu_file_path)
    else:
        score.pp, score.sr = calculate_rosu(score, osu_file_path)
