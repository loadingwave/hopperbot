import asyncio
import logging
import sys
from asyncio import Queue, Task
from typing import Union, cast

import tomllib

from hopperbot.secrets import tumblr_keys, twitter_keys
from hopperbot.tumblr import TumblrApi, TumblrPost
from hopperbot.twitter import TwitterListener

CONFIG_FILENAME = "config.toml"
CONFIG_CHANGED = True

logger = logging.getLogger("Main")
logger.setLevel(logging.DEBUG)


def initialise_identifiers(filename: str) -> dict[str, str]:
    with open(filename, "rb") as f:
        data: dict[str, list[dict[str, Union[str, list[dict[str, str]]]]]] = tomllib.load(f)

    if data is None:
        raise Exception("Reading config returned None")
    else:
        twitter_blognames = {
            k: v
            for d in [
                {
                    cast(str, twitter_update.get("username")).lower(): cast(str, update.get("blogname"))
                    for twitter_update in cast(list[dict[str, str]], update.get("Twitter", []))
                }
                for update in data.get("Update", [])
            ]
            for k, v in d.items()
        }
        logging.debug(f"Initalized twitter_blognames: {twitter_blognames}")

        return twitter_blognames


async def setup_twitter(queue: Queue[TumblrPost], usernames: list[str], tg: asyncio.TaskGroup) -> Task[None]:

    twitter_client = TwitterListener(queue, **twitter_keys)

    if CONFIG_CHANGED and usernames:
        await twitter_client.reset_rules()
        await twitter_client.add_usernames(usernames)

    expansions = [
        "author_id",
        "in_reply_to_user_id",
        "attachments.media_keys",
        "referenced_tweets.id",
    ]

    media_fields = ["alt_text", "type", "url"]

    # AsyncStreamingClient.filter() returns a task, that is why the return type
    # is "Task[None]" and not "None"
    return twitter_client.filter(tg=tg, expansions=expansions, media_fields=media_fields)


async def setup_tumblr(queue: Queue[TumblrPost], identifiers: dict[str, str]) -> None:
    tumblr_api = TumblrApi(**tumblr_keys)

    while True:
        update_post = await queue.get()
        if update_post.identifier is None:
            logger.error("Update post had no identifier?")
            blogname = "test37"
        else:
            blogname = identifiers.get(update_post.identifier, "test37")

        if blogname is None:
            logger.error("No blogname found?")
            blogname = "test37"

        await update_post.post(blogname, tumblr_api)
        queue.task_done()


def init_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    info_handler = logging.StreamHandler(sys.stderr)
    info_handler.setLevel(logging.INFO)
    info_formatter = logging.Formatter("%(name)-8s - %(levelname)-8s - %(message)s")
    info_handler.setFormatter(info_formatter)
    root_logger.addHandler(info_handler)

    debug_handler = logging.FileHandler("debug.log")
    debug_handler.setLevel(logging.DEBUG)
    debug_formatter = logging.Formatter("%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s")
    debug_handler.setFormatter(debug_formatter)
    root_logger.addHandler(debug_handler)


async def main() -> None:

    init_logging()

    # The work queue, things to update on are put in the queue, and when nothing
    # else is to be done, tumblr posts whatever is in the queue to tumblr
    queue: Queue[TumblrPost] = Queue()
    identifiers = initialise_identifiers(CONFIG_FILENAME)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(setup_tumblr(queue, identifiers))
        await setup_twitter(queue, list(identifiers.keys()), tg)


if __name__ == "__main__":
    with asyncio.Runner() as runner:
        runner.run(main())
