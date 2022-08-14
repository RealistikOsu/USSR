from __future__ import annotations

import asyncio
import traceback
from typing import Optional

import app.state
import logging
from app.models.user import User
import config

# This portion is based off cmyui's discord hooks code
# https://github.com/cmyui/cmyui_pkg/blob/master/cmyui/discord/webhook.py
class Footer:
    def __init__(self, text: str, **kwargs) -> None:
        self.text = text
        self.icon_url = kwargs.get("icon_url")
        self.proxy_icon_url = kwargs.get("proxy_icon_url")


class Image:
    def __init__(self, **kwargs) -> None:
        self.url = kwargs.get("url")
        self.proxy_url = kwargs.get("proxy_url")
        self.height = kwargs.get("height")
        self.width = kwargs.get("width")


class Thumbnail:
    def __init__(self, **kwargs) -> None:
        self.url = kwargs.get("url")
        self.proxy_url = kwargs.get("proxy_url")
        self.height = kwargs.get("height")
        self.width = kwargs.get("width")


class Video:
    def __init__(self, **kwargs) -> None:
        self.url = kwargs.get("url")
        self.height = kwargs.get("height")
        self.width = kwargs.get("width")


class Provider:
    def __init__(self, **kwargs) -> None:
        self.url = kwargs.get("url")
        self.name = kwargs.get("name")


class Author:
    def __init__(self, **kwargs) -> None:
        self.name = kwargs.get("name")
        self.url = kwargs.get("url")
        self.icon_url = kwargs.get("icon_url")
        self.proxy_icon_url = kwargs.get("proxy_icon_url")


class Field:
    def __init__(self, name: str, value: str, inline: bool = False) -> None:
        self.name = name
        self.value = value
        self.inline = inline


class Embed:
    def __init__(self, **kwargs) -> None:
        self.title = kwargs.get("title")
        self.type = kwargs.get("type")
        self.description = kwargs.get("description")
        self.url = kwargs.get("url")
        self.timestamp = kwargs.get("timestamp")  # datetime
        self.color = kwargs.get("color", 0x000000)

        self.footer: Optional[Footer] = kwargs.get("footer")
        self.image: Optional[Image] = kwargs.get("image")
        self.thumbnail: Optional[Thumbnail] = kwargs.get("thumbnail")
        self.video: Optional[Video] = kwargs.get("video")
        self.provider: Optional[Provider] = kwargs.get("provider")
        self.author: Optional[Author] = kwargs.get("author")

        self.fields: list[Field] = kwargs.get("fields", [])

    def set_footer(self, **kwargs) -> None:
        self.footer = Footer(**kwargs)

    def set_image(self, **kwargs) -> None:
        self.image = Image(**kwargs)

    def set_thumbnail(self, **kwargs) -> None:
        self.thumbnail = Thumbnail(**kwargs)

    def set_video(self, **kwargs) -> None:
        self.video = Video(**kwargs)

    def set_provider(self, **kwargs) -> None:
        self.provider = Provider(**kwargs)

    def set_author(self, **kwargs) -> None:
        self.author = Author(**kwargs)

    def add_field(self, name: str, value: str, inline: bool = False) -> None:
        self.fields.append(Field(name, value, inline))


class Webhook:
    """A class to represent a single-use Discord webhook."""

    __slots__ = ("url", "content", "username", "avatar_url", "tts", "file", "embeds")

    def __init__(self, url: str, **kwargs) -> None:
        self.url = url
        self.content = kwargs.get("content")
        self.username = kwargs.get("username")
        self.avatar_url = kwargs.get("avatar_url")
        self.tts = kwargs.get("tts")
        self.file = kwargs.get("file")
        self.embeds: list[Embed] = kwargs.get("embeds", [])

    def add_embed(self, embed: Embed) -> None:
        self.embeds.append(embed)

    @property
    def json(self):
        if not any([self.content, self.file, self.embeds]):
            raise Exception(
                "Webhook must contain atleast one " "of (content, file, embeds).",
            )

        if self.content and len(self.content) > 2000:
            raise Exception("Webhook content must be under " "2000 characters.")

        payload = {"embeds": []}

        for key in ("content", "username", "avatar_url", "tts", "file"):
            if (val := getattr(self, key)) is not None:
                payload[key] = val

        for embed in self.embeds:
            embed_payload = {}

            # simple params
            for key in ("title", "type", "description", "url", "timestamp", "color"):
                if val := getattr(embed, key):
                    embed_payload[key] = val

            # class params, must turn into dict
            for key in ("footer", "image", "thumbnail", "video", "provider", "author"):
                if val := getattr(embed, key):
                    embed_payload[key] = val.__dict__

            if embed.fields:
                embed_payload["fields"] = [f.__dict__ for f in embed.fields]

            payload["embeds"].append(embed_payload)

        return payload

    async def post(self) -> None:
        """Post the webhook in JSON format."""

        res: Optional[dict] = None
        async with app.state.services.http.post(self.url, data=self.json) as req:
            if req and req.status == 200:
                res = await req.json()

        if res:
            logging.debug(f"Webhook response: {res}")


async def wrap_hook(hook: str, embed: Embed) -> None:
    """Handles sending the webhook to discord."""

    logging.info("Sending Discord webhook!")

    try:
        wh = Webhook(hook, tts=False, username="LESS Score Server")
        wh.add_embed(embed)
        await wh.post()
    except Exception:
        logging.error(
            "Failed sending Discord webhook with exception " + traceback.format_exc(),
        )


def schedule_hook(hook: str, embed: Embed):
    """Performs a hook execution in a non-blocking manner."""

    if not hook:
        return

    loop = asyncio.get_event_loop()
    loop.create_task(wrap_hook(hook, embed))

    logging.debug("Scheduled the performing of a discord webhook!")


EDIT_COL = "4360181"
EDIT_ICON = "https://cdn3.iconfinder.com/data/icons/bold-blue-glyphs-free-samples/32/Info_Circle_Symbol_Information_Letter-512.png"

admin_hook = a_hook if (a_hook := config.DISCORD_ADMIN_HOOK) else None


async def log_user_edit(
    user: User,
    action: str,
    reason: str,
) -> None:
    """Logs a user edit action to the admin webhook."""

    embed = Embed(title="User Edited!", color=EDIT_COL)
    embed.description = (
        f"{user.name} ({user.id}) has just been {action}" f" for {reason}!"
    )
    embed.set_author(name="LESS Score Server", icon_url=EDIT_ICON)
    embed.set_footer(text="This is an automated action performed by the server.")

    schedule_hook(admin_hook, embed)
