from __future__ import annotations

import asyncio
import pprint

import aiohttp
import app.redis
import app.state
import app.usecases
import logger
import orjson
import settings
from fastapi import FastAPI
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import ORJSONResponse
from fastapi.responses import Response
from starlette.middleware.base import RequestResponseEndpoint


def init_events(asgi_app: FastAPI) -> None:
    @asgi_app.on_event("startup")
    async def on_startup() -> None:
        # TODO: maybe not here?
        if not settings.API_KEYS_POOL:
            logger.warning(
                "No osu!api v1 keys in the pool! Using fallback API v1 + osu.",
            )

        await app.state.services.database.connect()
        await app.state.services.redis.initialize()

        if settings.S3_ENABLED:
            await app.state.services.replay_storage.connect()

        app.state.services.http = aiohttp.ClientSession(
            json_serialize=lambda x: orjson.dumps(x).decode(),
        )

        await app.state.cache.init_cache()
        await app.redis.initialise_pubsubs()

        logger.info("Server has started!")

    @asgi_app.on_event("shutdown")
    async def on_shutdown() -> None:
        await app.state.cancel_tasks()

        await app.state.services.database.disconnect()
        await app.state.services.redis.close()

        if settings.S3_ENABLED:
            await app.state.services.replay_storage.disconnect()

        await app.state.services.http.close()

        logger.info("Server has shutdown!")

    @asgi_app.middleware("http")
    async def http_middleware(
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        try:
            return await call_next(request)
        except RuntimeError as err:
            if err.args[0] == "No response returned.":
                return Response("skill issue")

            raise err

    @asgi_app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        e: RequestValidationError,
    ) -> Response:
        return ORJSONResponse(
            content=jsonable_encoder(e.errors()),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


def init_fastapi() -> FastAPI:
    asgi_app = FastAPI()

    init_events(asgi_app)

    import app.api

    asgi_app.include_router(app.api.router)

    return asgi_app


asgi_app = init_fastapi()
