import asyncio
import logging
import sys
from asyncio import Queue, Task

from hopperbot import config
from hopperbot.debug import twitter_updatables
from hopperbot.database import init_database
from hopperbot.secrets import tumblr_keys, twitter_keys
from hopperbot.tumblr import TumblrApi, Update
from hopperbot.twitter import TwitterListener


async def setup_twitter(queue: Queue[Update]) -> Task[None]:
    twitter_client = TwitterListener(queue, **twitter_keys)

    if config.CHANGED:
        usernames = list(twitter_updatables.keys())
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


async def setup_tumblr(queue: Queue[Update]) -> None:
    tumblr_api = TumblrApi(**tumblr_keys)

    while True:
        update = await queue.get()
        await tumblr_api.post_update(update)
        queue.task_done()


async def main() -> None:

    # Setup logging (this prints to stderr, to redirect use >2 "filename" on Linux)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(name)-8s - %(levelname)-8s - %(message)s")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    init_database()

    # The work queue, things to update on are put in the queue, and when nothing
    # else is to be done, tumblr posts whatever is in the queue to tumblr
    queue: Queue[Update] = Queue()

    tumblr_task = asyncio.create_task(setup_tumblr(queue))
    twitter_task = await setup_twitter(queue)

    await twitter_task
    await tumblr_task


if __name__ == "__main__":
    asyncio.run(main())
