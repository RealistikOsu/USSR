from enum import IntFlag

class Mods(IntFlag):
    """osu! mod combination bitwise enums."""
    
    NOFAIL      = 1 << 0
    EASY        = 1 << 1
    TOUCHSCREEN = 1 << 2
    HIDDEN      = 1 << 3
    HARDROCK    = 1 << 4
    SUDDENDEATH = 1 << 5
    DOUBLETIME  = 1 << 6
    RELAX       = 1 << 7
    HALFTIME    = 1 << 8
    NIGHTCORE   = 1 << 9
    FLASHLIGHT  = 1 << 10
    AUTOPLAY    = 1 << 11
    SPUNOUT     = 1 << 12
    AUTOPILOT   = 1 << 13
    PERFECT     = 1 << 14
    KEY4        = 1 << 15
    KEY5        = 1 << 16
    KEY6        = 1 << 17
    KEY7        = 1 << 18
    KEY8        = 1 << 19
    FADEIN      = 1 << 20
    RANDOM      = 1 << 21
    CINEMA      = 1 << 22
    TARGET      = 1 << 23
    KEY9        = 1 << 24
    KEYCOOP     = 1 << 25
    KEY1        = 1 << 26
    KEY3        = 1 << 27
    KEY2        = 1 << 28
    SCOREV2     = 1 << 29
    MIRROR      = 1 << 30

    def rankable(self) -> bool:
        """Checks if the mod combo is rank-worthy."""

        if self & Mods.AUTOPLAY: return False
        # TODO: Expand this
        return True
    
    def conflict(self) -> bool:
        """Anticheat measure to check for illegal mod combos."""

        if self & Mods.DOUBLETIME and self & Mods.HALFTIME: return True
        elif self & Mods.NIGHTCORE and not self & Mods.DOUBLETIME: return True
        elif self & Mods.EASY and self & Mods.HARDROCK: return True

        # TODO: Expand this.

        return False

    @property
    def readable(self) -> str:
        """Turns the mod bitwise value and turns it into a readable string."""

        m = int(self)
        if not m: return 'NM'

        r = []
        if m & self.NOFAIL:      r.append('NF')
        if m & self.EASY:        r.append('EZ')
        if m & self.TOUCHSCREEN: r.append('TD')
        if m & self.HIDDEN:      r.append('HD')
        if m & self.HARDROCK:    r.append('HR')
        if m & self.HALFTIME:    r.append('HT')
        if m & self.NIGHTCORE:   r.append('NC')
        elif m & self.DOUBLETIME:  r.append('DT')
        if m & self.FLASHLIGHT:  r.append('FL')
        if m & self.SPUNOUT:     r.append('SO')
        if m & self.RELAX:     r.append('RX')
        if m & self.AUTOPILOT:     r.append('AP')
        if m & self.MIRROR:      r.append('MR')
        if m & self.KEY1:        r.append('1K')
        if m & self.KEY2:        r.append('2K')
        if m & self.KEY3:        r.append('3K')
        if m & self.KEY4:        r.append('4K')
        if m & self.KEY5:        r.append('5K')
        if m & self.KEY6:        r.append('6K')
        if m & self.KEY7:        r.append('7K')
        if m & self.KEY8:        r.append('8K')
        if m & self.KEY9:        r.append('9K')
        return ''.join(r)
