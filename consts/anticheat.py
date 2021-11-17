# Constants related to the anticheat system.
from enum import IntEnum

class LastFMFlags(IntEnum):
    """Bitwise enum flags for osu's LastFM anticheat flags (aka `BadFlags`)."""

    # 2016 Anticheat (from source)
    TIMEWARP = 1 << 1 # Saw this one get triggered during intense lag. Compares song speed to time elapsed.
    INCORRECT_MOD_VALUE = 1 << 2 # Cheat attempted to alter the mod values incorrectly
    MULTIPLE_OSU_CLIENTS = 1 << 3
    CHECKSUM_FAIL = 1 << 4 # Cheats that modify memory to unrealistic values.
    FLASHLIGHT_CHECKSUM_FAIL = 1 << 5
    
    # These 2 are server side 
    OSU_EXE_CHECKSUM_FAIL = 1 << 6
    MISSING_PROCESS = 1 << 7

    FLASHLIGHT_REMOVER = 1 << 8 # Checks actual pixels on the screen
    AUTOSPIN_HACK = 1 << 9 # Unused in 2016 src
    WINDOW_OVERLAY = 1 << 10 # There is a transparent window overlaying osu (cheat uis)
    FAST_PRESS = 1 << 11 # Mania only. dont understand it fully. 

    # These check if there is something altering the cursor pos/kb being received
    # through comparing the raw input.
    MOUSE_DISCREPENCY = 1 << 12
    KB_DISCREPENCY = 1 << 13

    # These are taken from `gulag` https://github.com/cmyui/gulag/blob/master/constants/clientflags.py
    # They relate to the new 2019 lastfm extension introducing measures against AQN and HQOsu.
    LF_FLAG_PRESENT = 1 << 14
    OSU_DEBUGGED = 1 << 15 # A console attached to the osu process is running.
    EXTRA_THREADS = 1 << 16 # Osu cheats usually create a new thread to run it. This aims to detect them.

    # HQOsu specific ones.
    HQOSU_ASSEMBLY = 1 << 17
    HQOSU_FILE = 1 << 18
    HQ_RELIFE = 1 << 19 # Detects registry edits left by Relife

    # (Outdated) AQN detection methods
    AQN_SQL2LIB = 1 << 20
    AQN_LIBEAY32 = 1 << 21
    AQN_MENU_SOUND = 1 << 22
