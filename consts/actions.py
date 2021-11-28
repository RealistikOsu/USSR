from enum import IntFlag

class Actions(IntFlag):
    """Bitwise enumerations for user edit action."""
    UNBAN = 1 << 0
    UNRESTRICT = 1 << 1
    RESTRICT = 1 << 2
    BAN = 1 << 3

    @property
    def log_action(self):
        return _actions[self]

_actions = {
    Actions.UNBAN: "unbanned",
    Actions.UNRESTRICT: "unrestricted",
    Actions.RESTRICT: "restricted",
    Actions.BAN: "banned"
}
