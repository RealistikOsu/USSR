from __future__ import annotations

import httpx
from fastapi import status
from tenacity import retry_if_exception


class retry_if_exception_network_related(retry_if_exception):
    """Retries if an exception is from a network related failure."""

    def __init__(self) -> None:
        def predicate(exc: BaseException) -> bool:
            if isinstance(exc, httpx.HTTPStatusError):
                if exc.response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                    # TODO: 3rd parties may have specific retry-after headers
                    #       that we should/can respect for better performance
                    return True
            elif isinstance(exc, httpx.NetworkError):
                return True
            return False

        super().__init__(predicate)
