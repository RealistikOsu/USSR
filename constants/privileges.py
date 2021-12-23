# Ripple privileges. Taken from the Ripple common module
# https://github.com/osuripple/ripple-python-common/blob/master/constants/privileges.py
from enum import IntFlag

class Privileges(IntFlag):
    """Bitwise enumerations for Ripple privileges."""

    USER_PUBLIC               = 1
    USER_NORMAL               = 2 << 0
    USER_DONOR                = 2 << 1
    ADMIN_ACCESS_RAP          = 2 << 2
    ADMIN_MANAGE_USERS        = 2 << 3
    ADMIN_BAN_USERS           = 2 << 4
    ADMIN_SILENCE_USERS       = 2 << 5
    ADMIN_WIPE_USERS          = 2 << 6
    ADMIN_MANAGE_BEATMAPS     = 2 << 7
    ADMIN_MANAGE_SERVERS      = 2 << 8
    ADMIN_MANAGE_SETTINGS     = 2 << 9
    ADMIN_MANAGE_BETAKEYS     = 2 << 10
    ADMIN_MANAGE_REPORTS      = 2 << 11
    ADMIN_MANAGE_DOCS         = 2 << 12
    ADMIN_MANAGE_BADGES       = 2 << 13
    ADMIN_VIEW_RAP_LOGS       = 2 << 14
    ADMIN_MANAGE_PRIVILEGES   = 2 << 15
    ADMIN_SEND_ALERTS         = 2 << 16
    ADMIN_CHAT_MOD            = 2 << 17
    ADMIN_KICK_USERS          = 2 << 18
    USER_PENDING_VERIFICATION = 2 << 19
    USER_TOURNAMENT_STAFF     = 2 << 20
    ADMIN_CAKER               = 20 << 21

    @property
    def is_restricted(self) -> bool:
        """Checks if user is restricted."""
        return (self & Privileges.USER_NORMAL) and not (self & Privileges.USER_PUBLIC)
    
    @property
    def is_banned(self) -> bool:
        """Checks if user is banned."""
        return not (self & Privileges.USER_PUBLIC | Privileges.USER_NORMAL > 0)

    def has_privilege(self, priv: 'Privileges') -> bool:
        """Returns a bool corresponding to whether the privilege flag contains
        a single privilege.
        
        Note:
            This is a check for a **singular** privilege. If you include
                multiple, just the presence of one would result in
                `True` being returned.
        """

        # Looks weird but fastest way to turn into bool.
        return not not self & priv
