# A cool discord helper (specifically with webhooks)
import traceback
from dhooks import Webhook, Embed, embed
from config import conf
import asyncio
from consts.actions import Actions
from typing import TYPE_CHECKING

from logger import debug, error, info

if TYPE_CHECKING:
    from objects.score import Score

# Hooks
admin_hook = Webhook.Async(conf.discord_admin_hook) if conf.discord_admin_hook else None
first_hook = Webhook.Async(conf.discord_first_hook) if conf.discord_first_hook else None

async def wrap_hook(hook: Webhook, embed: Embed) -> None:
    """Handles sending the webhook to discord."""

    info("Sending Discord webhook!")
    try: await hook.send(embed= embed)
    except Exception:
        error("Failed sending Discord webhook with exception "
              + traceback.format_exc())

async def schedule_hook(hook: Webhook, embed: Embed):
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
    embed.set_footer("This is an automated action performed by the server.")

    await schedule_hook(admin_hook, embed)

async def log_first_place(s: 'Score') -> None:
    """Logs a user's first place to the first place webhook."""

    # Heavily inspired by Ainu's webhook style.
    embed = Embed(color=0x0f97ff)
    embed.set_footer("USSR Score Server")
    embed.set_title(f"New #1 score set by {s.username}!")
    embed.description = (
        f"[{s.c_mode.acronym}] {s.username} achieved a #1 score on "
        f"**{s.bmap.song_name}** +{s.mods.readable} ({s.pp:.2f})"
    )

    embed.set_image(f"https://assets.ppy.sh/beatmaps/{s.bmap.set_id}/covers/cover.jpg")

    await schedule_hook(first_hook, embed)
