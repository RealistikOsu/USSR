# A cool discord helper (specifically with webhooks)
import traceback
from config import conf
import asyncio
from consts.actions import Actions
from typing import TYPE_CHECKING, Optional
from conn.web_client import simple_post_json
from logger import debug, error, info

if TYPE_CHECKING:
    from objects.score import Score

# This portion is based off cmyui's discord hooks code
# https://github.com/cmyui/cmyui_pkg/blob/master/cmyui/discord/webhook.py
class Footer:
    def __init__(self, text: str, **kwargs) -> None:
        self.text = text
        self.icon_url = kwargs.get('icon_url')
        self.proxy_icon_url = kwargs.get('proxy_icon_url')

class Image:
    def __init__(self, **kwargs) -> None:
        self.url = kwargs.get('url')
        self.proxy_url = kwargs.get('proxy_url')
        self.height = kwargs.get('height')
        self.width = kwargs.get('width')

class Thumbnail:
    def __init__(self, **kwargs) -> None:
        self.url = kwargs.get('url')
        self.proxy_url = kwargs.get('proxy_url')
        self.height = kwargs.get('height')
        self.width = kwargs.get('width')

class Video:
    def __init__(self, **kwargs) -> None:
        self.url = kwargs.get('url')
        self.height = kwargs.get('height')
        self.width = kwargs.get('width')

class Provider:
    def __init__(self, **kwargs) -> None:
        self.url = kwargs.get('url')
        self.name = kwargs.get('name')

class Author:
    def __init__(self, **kwargs) -> None:
        self.name = kwargs.get('name')
        self.url = kwargs.get('url')
        self.icon_url = kwargs.get('icon_url')
        self.proxy_icon_url = kwargs.get('proxy_icon_url')

class Field:
    def __init__(self, name: str, value: str,
                 inline: bool = False) -> None:
        self.name = name
        self.value = value
        self.inline = inline

class Embed:
    def __init__(self, **kwargs) -> None:
        self.title = kwargs.get('title')
        self.type = kwargs.get('type')
        self.description = kwargs.get('description')
        self.url = kwargs.get('url')
        self.timestamp = kwargs.get('timestamp') # datetime
        self.color = kwargs.get('color', 0x000000)

        self.footer: Optional[Footer] = kwargs.get('footer')
        self.image: Optional[Image] = kwargs.get('image')
        self.thumbnail: Optional[Thumbnail] = kwargs.get('thumbnail')
        self.video: Optional[Video] = kwargs.get('video')
        self.provider: Optional[Provider] = kwargs.get('provider')
        self.author: Optional[Author] = kwargs.get('author')

        self.fields: list[Field] = kwargs.get('fields', [])

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

    def add_field(self, name: str, value: str,
                  inline: bool = False) -> None:
        self.fields.append(Field(name, value, inline))

class Webhook:
    """A class to represent a single-use Discord webhook."""
    __slots__ = ('url', 'content', 'username',
                 'avatar_url', 'tts', 'file', 'embeds')
    def __init__(self, url: str, **kwargs) -> None:
        self.url = url
        self.content = kwargs.get('content')
        self.username = kwargs.get('username')
        self.avatar_url = kwargs.get('avatar_url')
        self.tts = kwargs.get('tts')
        self.file = kwargs.get('file')
        self.embeds: list[Embed] = kwargs.get('embeds', [])

    def add_embed(self, embed: Embed) -> None:
        self.embeds.append(embed)

    @property
    def json(self):
        if not any([self.content, self.file, self.embeds]):
            raise Exception('Webhook must contain atleast one '
                            'of (content, file, embeds).')

        if self.content and len(self.content) > 2000:
            raise Exception('Webhook content must be under '
                            '2000 characters.')

        payload = {'embeds': []}

        for key in ('content', 'username',
                    'avatar_url', 'tts', 'file'):
            if (val := getattr(self, key)) is not None:
                payload[key] = val

        for embed in self.embeds:
            embed_payload = {}

            # simple params
            for key in ('title', 'type', 'description',
                        'url', 'timestamp', 'color'):
                if val := getattr(embed, key):
                    embed_payload[key] = val

            # class params, must turn into dict
            for key in ('footer', 'image', 'thumbnail',
                        'video', 'provider', 'author'):
                if val := getattr(embed, key):
                    embed_payload[key] = val.__dict__

            if embed.fields:
                embed_payload['fields'] = [f.__dict__ for f in embed.fields]

            payload['embeds'].append(embed_payload)

        return payload

    async def post(self) -> None:
        """Post the webhook in JSON format."""

        res = await simple_post_json(self.url, self.json, False)
        debug(f"Webhook response: {res}")

# Hooks
admin_hook = conf.discord_admin_hook if conf.discord_admin_hook else None
first_hook = conf.discord_first_hook if conf.discord_first_hook else None

async def wrap_hook(hook: str, embed: Embed) -> None:
    """Handles sending the webhook to discord."""

    info("Sending Discord webhook!")
    try:
        wh = Webhook(
            hook,
            tts= False,
            username= "USSR Score Server"
        )
        wh.add_embed(embed)
        await wh.post()
    except Exception:
        error("Failed sending Discord webhook with exception "
              + traceback.format_exc())

async def schedule_hook(hook: str, embed: Embed):
    """Performs a hook execution in a non-blocking manner."""

    if not hook: return
    loop = asyncio.get_event_loop()
    loop.create_task(wrap_hook(hook, embed))
    debug("Scheduled the performing of a discord webhook!")

EDIT_COL = "4360181"
EDIT_ICON = "https://cdn3.iconfinder.com/data/icons/bold-blue-glyphs-free-samples/32/Info_Circle_Symbol_Information_Letter-512.png"
async def log_user_edit(user_id: int, username: str, action: Actions, reason: str) -> None:
    """Logs a user edit action to the admin webhook."""

    embed = Embed(title="User Edited!", color=EDIT_COL)
    embed.description = (f"{username} ({user_id}) has just been {action.log_action}"
                        f" for {reason}!")
    embed.set_author(name="USSR Score Server", icon_url=EDIT_ICON)
    embed.set_footer(text= "This is an automated action performed by the server.")

    await schedule_hook(admin_hook, embed)

