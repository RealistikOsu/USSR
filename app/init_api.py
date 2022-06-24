from __future__ import annotations

import asyncio
import contextlib
import pprint

import aiobotocore.session
import aiohttp
import orjson
from fastapi import FastAPI
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import ORJSONResponse
from fastapi.responses import Response
from starlette.middleware.base import RequestResponseEndpoint

import app.redis
import app.state
import app.usecases
import logger
from config import config

ctx_stack = contextlib.AsyncExitStack()


def init_events(asgi_app: FastAPI) -> None:
    @asgi_app.on_event("startup")
    async def on_startup() -> None:
        await app.state.services.database.connect()
        await app.state.services.redis.initialize()

        app.state.services.http = aiohttp.ClientSession(
            json_serialize=lambda x: orjson.dumps(x).decode(),
        )

        app.state.services.s3_client = await ctx_stack.enter_async_context(
            aiobotocore.session.get_session().create_client(  # type: ignore
                "s3",
                region_name=config.AWS_REGION,
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                endpoint_url=config.AWS_ENDPOINT_URL,
            ),
        )

        await app.state.cache.init_cache()
        await app.redis.initialise_pubsubs()

        for _task in (
            app.usecases.privileges.update_privileges_task,
            app.usecases.usernames.update_usernames_task,
            app.usecases.countries.update_countries_task,
            app.usecases.clans.update_clans_task,
            app.usecases.pp_cap.update_pp_cap_task,
            app.usecases.whitelist.update_whitelist_task,
        ):
            task = asyncio.create_task(_task())
            app.state.tasks.add(task)

        logger.info("Server has started!")
        logger.write_log_file("Server has started!")

    @asgi_app.on_event("shutdown")
    async def on_shutdown() -> None:
        await app.state.cancel_tasks()

        await app.state.services.database.disconnect()
        await app.state.services.redis.close()

        await app.state.services.http.close()

        await ctx_stack.aclose()

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
        logger.write_log_file(
            f"Validation error on {request.url}:\n{pprint.pformat(e.errors())}",
        )

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
