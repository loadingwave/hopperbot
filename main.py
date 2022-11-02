import asyncio
import logging
import os
import sys
from asyncio import Queue

from pytumblr2 import TumblrRestClient as TumblrApi
from tweepy import StreamRule
from tweepy.asynchronous import AsyncClient as TwitterApi

from hopperbot.config import blogname
from hopperbot.config import updatables
from hopperbot.hoppertasks import Update, TwitterUpdate
from hopperbot.renderer import Renderer
from hopperbot.secrets import tumblr_keys, twitter_keys
from hopperbot.twitter import TwitterListener


# Included for debugging purposes
async def printing(queue: Queue[Update]) -> None:
    while True:
        logging.info(f"[Main] Queue empty: {queue.empty()}")
        await asyncio.sleep(5)


async def setup_twitter(queue: Queue[Update]) -> asyncio.Task[None]:
    twitter_api = TwitterApi(**twitter_keys)
    twitter_client = TwitterListener(queue, twitter_api, **twitter_keys)

    rule = StreamRule(" OR ".join(map(lambda x: "from:" + x, updatables)), "ranboo")

    await twitter_client.add_rules(rule)

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
    logging.info("[Tumblr] Initialized Tumblr api")
    renderer = Renderer()
    logging.debug("[Tumblr] Initialized renderer")

    while True:
        logging.debug("[Tumblr] Fetching task...")
        t = await queue.get()
        logging.info(f'[Tumblr] consuming task "{t.identifier}"')

        if isinstance(t, TwitterUpdate):
            # Rendering has to be blocking because the external webdriver is a black box
            filenames = renderer.render_tweets(t.url, t.identifier, t.tweet_index, t.thread_height)

            media_sources = {f"tweet{i}": filename for (i, filename) in enumerate(filenames)}

            response = tumblr_api.create_post(
                blogname=blogname,
                content=t.content,
                tags=["hp.automated", "hp.twitter"],
                media_sources=media_sources,
            )

            if "meta" in response:
                logging.error(f"[Tumblr] {response}")
            else:
                logging.debug(f"[Tumblr] {response}")

            # After the files have been uploaded to Tumblr, we don't want them to gobble up our memory
            for filename in filenames:
                os.remove(filename)
        else:
            logging.warning(f'[Tumblr] unrecognised HopperTask "{t.identifier}"')
        queue.task_done()


async def main() -> None:

    # Setup logging (this prints to stderr, to redirect use >2 "filename" on Linux)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

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
