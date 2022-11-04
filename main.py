import asyncio
import logging
import sqlite3 as sqlite
import sys
from asyncio import Queue, Task

from hopperbot import config
from hopperbot.config import twitter_updatables
from hopperbot.people import Person, adapt_person, convert_person
from hopperbot.renderer import Renderer
from hopperbot.secrets import tumblr_keys, twitter_keys
from hopperbot.twitter import TwitterListener
from hopperbot.updates import Update
from hopperbot.tumblr import TumblrApi


async def setup_twitter(queue: Queue[Update]) -> Task[None]:
    twitter_client = TwitterListener(queue, **twitter_keys)

    if config.CHANGED:
        usernames = list(twitter_updatables.keys())
        await twitter_client.reset_rules()
        await twitter_client.add_rules(usernames)
        config.CHANGED = False

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
    logging.info("Initialized Tumblr api")
    renderer = Renderer()
    logging.debug("Initialized renderer")

    kwargs = {"renderer": renderer, "twitter_token": twitter_keys["bearer_token"]}

    while True:
        update = await queue.get()
        await tumblr_api.post_update(update, **kwargs)
        queue.task_done()


def touch_tweets_db() -> None:
    con = sqlite.connect("tweets.db", detect_types=sqlite.PARSE_DECLTYPES)
    cur = con.cursor()

    response = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tweets'").fetchone()

    if response is None:
        logging.info("[Main] Created table")
        cur.execute(
            "CREATE TABLE tweets(tweet_id INTEGER PRIMARY KEY, tweet_index INTEGER, reblog_id INTEGER, blogname STRING)"
        )

    con.commit()
    con.close()


async def main() -> None:

    # Setup logging (this prints to stderr, to redirect use >2 "filename" on Linux)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    sqlite.register_adapter(Person, adapt_person)
    sqlite.register_converter("PERSON", convert_person)

    touch_tweets_db()

    # The work queue, things to update on are put in the queue, and when nothing
    # else is to be done, tumblr posts whatever is in the queue to tumblr
    queue: Queue[Update] = Queue()

    tumblr_task = asyncio.create_task(setup_tumblr(queue))
    logging.debug("[Main] Starting Tumblr task")

    twitter_task = await setup_twitter(queue)
    logging.debug("[Main] Starting Twitter task")

    await twitter_task
    await tumblr_task


if __name__ == "__main__":
    asyncio.run(main())
