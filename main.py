import asyncio
import logging
import sys
from asyncio import Queue, Task

from hopperbot.secrets import tumblr_keys, twitter_keys
from hopperbot.tumblr import TumblrApi, TumblrPost
from hopperbot.twitter import TwitterListener
from hopperbot.config import init_twitter_blognames

CONFIG_FILENAME = "config.toml"
CONFIG_CHANGED = False


async def setup_twitter(queue: Queue[TumblrPost]) -> Task[None]:

    usernames = list(init_twitter_blognames(CONFIG_FILENAME).keys())

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
    return twitter_client.filter(expansions=expansions, media_fields=media_fields)


async def setup_tumblr(queue: Queue[TumblrPost]) -> None:
    tumblr_api = TumblrApi(**tumblr_keys)

    while True:
        update_post = await queue.get()
        response = await update_post.post("test37", tumblr_api)
        if not response:
            logging.error("Tumblr response was wrong")
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

    tumblr_task = asyncio.create_task(setup_tumblr(queue))
    twitter_task = await setup_twitter(queue)

    await twitter_task
    await tumblr_task


if __name__ == "__main__":
    asyncio.run(main())
