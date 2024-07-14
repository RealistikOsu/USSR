from __future__ import annotations

from enum import IntFlag


class Privileges(IntFlag):
    """Bitwise enumerations for Ripple privileges."""

    USER_PUBLIC = 1 << 0
    USER_NORMAL = 1 << 1
    USER_DONOR = 1 << 2
    ADMIN_ACCESS_RAP = 1 << 3
    ADMIN_MANAGE_USERS = 1 << 4
    ADMIN_BAN_USERS = 1 << 5
    ADMIN_SILENCE_USERS = 1 << 6
    ADMIN_WIPE_USERS = 1 << 7
    ADMIN_MANAGE_BEATMAPS = 1 << 8
    ADMIN_MANAGE_SERVERS = 1 << 9
    ADMIN_MANAGE_SETTINGS = 1 << 10
    ADMIN_MANAGE_BETAKEYS = 1 << 11
    ADMIN_MANAGE_REPORTS = 1 << 12
    ADMIN_MANAGE_DOCS = 1 << 13
    ADMIN_MANAGE_BADGES = 1 << 14
    ADMIN_VIEW_RAP_LOGS = 1 << 15
    ADMIN_MANAGE_PRIVILEGES = 1 << 16
    ADMIN_SEND_ALERTS = 1 << 17
    ADMIN_CHAT_MOD = 1 << 18
    ADMIN_KICK_USERS = 1 << 19
    USER_PENDING_VERIFICATION = 1 << 20
    USER_TOURNAMENT_STAFF = 1 << 21
    ADMIN_CAKER = 1 << 22
    USER_PREMIUM = 1 << 23
    ADMIN_FREEZE_USERS = 1 << 24
    ADMIN_MANAGE_NOMINATORS = 1 << 25

    @property
    def is_restricted(self) -> bool:
        """Checks if user is restricted."""
        return self & Privileges.USER_PUBLIC == 0

    @property
    def is_banned(self) -> bool:
        """Checks if user is banned."""
        return self & Privileges.USER_NORMAL == 0

    def has_privilege(self, priv: Privileges) -> bool:
        """Returns a bool corresponding to whether the privilege flag contains
        a single privilege.
        Note:
            This is a check for a **singular** privilege. If you include
                multiple, just the presence of one would result in
                `True` being returned.
        """

        return self & priv != 0
