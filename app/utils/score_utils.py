from __future__ import annotations


def calculate_accuracy(
    *,
    n300: int,
    n100: int,
    n50: int,
    ngeki: int,
    nkatu: int,
    nmiss: int,
    vanilla_mode: int,
) -> float:
    if vanilla_mode == 0:  # osu!
        total = n300 + n100 + n50 + nmiss

        if total == 0:
            return 0.0

        return (
            100.0 * ((n300 * 300.0) + (n100 * 100.0) + (n50 * 50.0)) / (total * 300.0)
        )

    elif vanilla_mode == 1:  # osu!taiko
        total = n300 + n100 + nmiss

        if total == 0:
            return 0.0

        return 100.0 * ((n100 * 0.5) + n300) / total

    elif vanilla_mode == 2:  # osu!catch
        total = n300 + n100 + n50 + nkatu + nmiss

        if total == 0:
            return 0.0

        return 100.0 * (n300 + n100 + n50) / total

    elif vanilla_mode == 3:  # osu!mania
        total = n300 + n100 + n50 + ngeki + nkatu + nmiss

        if total == 0:
            return 0.0

        return (
            100.0
            * (
                (n50 * 50.0)
                + (n100 * 100.0)
                + (nkatu * 200.0)
                + ((n300 + ngeki) * 300.0)
            )
            / (total * 300.0)
        )
    else:
        raise NotImplementedError(f"Unknown mode: {vanilla_mode}")


def calculate_grade(
    *,
    vanilla_mode: int,
    mods: int,
    acc: float,
    n300: int,
    n100: int,
    n50: int,
    nmiss: int,
) -> str:
    objectCount = n300 + n100 + n50 + nmiss
    shouldUseSilverGrades = (mods & 1049608) > 0
    if vanilla_mode == 0:  # osu!
        ratio300 = n300 / objectCount
        ratio50 = n50 / objectCount
        if ratio300 == 1:
            return "XH" if shouldUseSilverGrades else "X"
        if ratio300 > 0.9 and ratio50 <= 0.01 and nmiss == 0:
            return "SH" if shouldUseSilverGrades else "S"
        if ratio300 > 0.8 and nmiss == 0 or ratio300 > 0.9:
            return "A"
        if ratio300 > 0.7 and nmiss == 0 or ratio300 > 0.8:
            return "B"
        if ratio300 > 0.6:
            return "C"
        return "D"
    elif vanilla_mode == 1:  # osu!taiko
        ratio300 = n300 / objectCount
        ratio50 = n50 / objectCount
        if ratio300 == 1:
            return "XH" if shouldUseSilverGrades else "X"
        if ratio300 > 0.9 and ratio50 <= 0.01 and nmiss == 0:
            return "SH" if shouldUseSilverGrades else "S"
        if ratio300 > 0.8 and nmiss == 0 or ratio300 > 0.9:
            return "A"
        if ratio300 > 0.7 and nmiss == 0 or ratio300 > 0.8:
            return "B"
        if ratio300 > 0.6:
            return "C"
        return "D"
    elif vanilla_mode == 2:  # osu!catch
        if acc == 100:
            return "XH" if shouldUseSilverGrades else "X"
        if acc > 98:
            return "SH" if shouldUseSilverGrades else "S"
        if acc > 94:
            return "A"
        if acc > 90:
            return "B"
        if acc > 85:
            return "C"
        return "D"
    elif vanilla_mode == 3:  # osu!mania
        if acc == 100:
            return "XH" if shouldUseSilverGrades else "X"
        if acc > 95:
            return "SH" if shouldUseSilverGrades else "S"
        if acc > 90:
            return "A"
        if acc > 80:
            return "B"
        if acc > 70:
            return "C"
        return "D"
    else:
        raise NotImplementedError(f"Unknown mode: {vanilla_mode}")
