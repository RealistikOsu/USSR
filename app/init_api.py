from __future__ import annotations

import contextlib
import logging
import pprint

import aio_pika
import aiobotocore.session
import httpx
import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import ORJSONResponse
from fastapi.responses import Response
from starlette.middleware.base import RequestResponseEndpoint

import app.state
import app.usecases
import config
from app import job_scheduling

ctx_stack = contextlib.AsyncExitStack()


def init_events(asgi_app: FastAPI) -> None:
    @asgi_app.on_event("startup")
    async def on_startup() -> None:
        await app.state.services.database.connect()

        # explicitly providing username & password as non None will call the AUTH cmd
        # which will fail if a password is not set.
        # if they're not using the default user then it should explicitly auth as that user
        # however it will fail if they have no password set
        # but this is still better than implicitly working as the default one
        should_send_redis_authentication = (
            config.REDIS_PASS != "" or config.REDIS_USER != "default"
        )
        app.state.services.redis = aioredis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            username=config.REDIS_USER if should_send_redis_authentication else None,
            password=config.REDIS_PASS if should_send_redis_authentication else None,
            ssl=config.REDIS_USE_SSL,
        )
        await app.state.services.redis.initialize()
        await app.state.services.redis.ping()

        app.state.services.http_client = httpx.AsyncClient()

        app.state.services.s3_client = None
        if (
            config.AWS_ENDPOINT_URL
            and config.AWS_REGION
            and config.AWS_ACCESS_KEY_ID
            and config.AWS_SECRET_ACCESS_KEY
        ):
            app.state.services.s3_client = await ctx_stack.enter_async_context(
                aiobotocore.session.get_session().create_client(  # type: ignore
                    "s3",
                    region_name=config.AWS_REGION,
                    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                    endpoint_url=config.AWS_ENDPOINT_URL,
                ),
            )

        app.state.services.amqp = None
        app.state.services.amqp_channel = None
        if (
            config.AMQP_USER
            and config.AMQP_PASS
            and config.AMQP_HOST
            and config.AMQP_PORT
        ):
            app.state.services.amqp = await aio_pika.connect_robust(
                f"amqp://{config.AMQP_USER}:{config.AMQP_PASS}@{config.AMQP_HOST}:{config.AMQP_PORT}/",
            )

            app.state.services.amqp_channel = await app.state.services.amqp.channel()

        await app.state.cache.init_cache()

        logging.info("Server has started!")

    @asgi_app.on_event("shutdown")
    async def on_shutdown() -> None:
        await job_scheduling.await_running_jobs(timeout=7.5)

        await app.state.services.database.disconnect()

        await app.state.services.redis.close()

        await app.state.services.http_client.aclose()

        if app.state.services.amqp_channel is not None:
            await app.state.services.amqp_channel.close()

        if app.state.services.amqp is not None:
            await app.state.services.amqp.close()

        await ctx_stack.aclose()

        logging.info("Server has shutdown!")

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
        logging.error(
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
