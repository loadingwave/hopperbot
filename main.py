import asyncio
import logging
import os
import sys
from asyncio import Queue

from pytumblr2 import TumblrRestClient as TumblrApi
from tweepy import StreamRule
from tweepy.asynchronous import AsyncClient as TwitterApi

from hopperbot.config import updatables
from hopperbot.hoppertasks import HopperTask, TwitterTask
from hopperbot.renderer import Renderer
from hopperbot.secrets import tumblr_keys, twitter_keys
from hopperbot.twitter import TwitterListener

BLOGNAME = "test37"


async def printing() -> None:
    while True:
        logging.debug("[Main] ...")
        await asyncio.sleep(5)


async def setup_twitter(queue: Queue[HopperTask]) -> asyncio.Task[None]:
    twitter_api = TwitterApi(**twitter_keys)
    twitter_client = TwitterListener(queue, twitter_api, **twitter_keys)

    ranboo_rule = StreamRule(
        " OR ".join(map(lambda x: "from:" + x, updatables)), "ranboo"
    )

    await twitter_client.add_rules(ranboo_rule)

    expansions = [
        "author_id",
        "in_reply_to_user_id",
        "attachments.media_keys",
        "referenced_tweets.id",
    ]

    media_fields = ["alt_text", "type", "url"]

    return twitter_client.filter(expansions=expansions, media_fields=media_fields)


async def setup_tumblr(queue: Queue[HopperTask]) -> None:
    tumblr_api = TumblrApi(**tumblr_keys)
    logging.debug("[Tumblr] Initialized Tumblr api")
    renderer = Renderer()
    logging.debug("[Tumblr] Initialized renderer")
    while True:
        t = await queue.get()
        logging.info("[Tumblr] Got task")
        if isinstance(t, TwitterTask):
            # Rendering has to be blocking because the external webdriver is a black box
            filenames = renderer.render_tweets(
                t.url, t.filename_prefix, t.tweet_index, t.thread_height
            )
            logging.debug("[Tumblr] filenames: {}".format(filenames))
            media_sources = {
                "tweet{}".format(i): filename for (i, filename) in enumerate(filenames)
            }
            response = tumblr_api.create_post(
                blogname=BLOGNAME,
                content=t.content,
                tags=["hp.automated", "hp.twitter"],
                media_sources=media_sources,
            )

            if "meta" in response:
                logging.error("[Tumblr] {}".format(response))
            else:
                logging.debug("[Tumblr] {}".format(response))

            for filename in filenames:
                os.remove(filename)
        else:
            logging.warning("[Tumblr] unrecognised HopperTask")


async def main() -> None:

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    queue: Queue[HopperTask] = Queue()

    logging.debug("[Main] Setup Logger")
    twitter_task = await setup_twitter(queue)
    logging.debug("[Main] Started Twitter task")
    tumblr_task = asyncio.create_task(setup_tumblr(queue))
    logging.debug("[Main] Start Tumblr task")

    printing_task = asyncio.create_task(printing())

    await printing_task
    await twitter_task
    await tumblr_task


if __name__ == "__main__":
    asyncio.run(main())
