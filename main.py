import asyncio
import logging
import os
import sys
from asyncio import Queue

from tweepy import StreamRule
from tweepy.asynchronous import AsyncClient as TwitterApi
from pytumblr2 import TumblrRestClient as TumblrApi

from hopperbot.secrets import twitter_keys, tumblr_keys
from hopperbot.twitter import TwitterListener
from hopperbot.renderer import Renderer
from hopperbot.hoppertasks import HopperTask, TwitterTask


BLOGNAME = "Test37"


async def printing() -> None:
    for i in range(50):
        print("[Printing] ", i)
        await asyncio.sleep(5)


async def setup_twitter(queue: Queue[HopperTask]) -> asyncio.Task[None]:
    twitter_api = TwitterApi(**twitter_keys)
    twitter_client = TwitterListener(queue, twitter_api, **twitter_keys)

    rule = StreamRule(
        "from:space_stew OR from:tapwaterthomas OR from:Etherealbro_", "rule1"
    )

    await twitter_client.add_rules(rule)

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
    renderer = Renderer()
    while True:
        t = await queue.get()
        if isinstance(t, TwitterTask):
            filenames = await renderer.render_tweets(
                t.url, t.filename_prefix, t.tweet_index, t.thread_height
            )
            media_sources = {
                "tweet{}".format(i): filename for (i, filename) in enumerate(filenames)
            }
            response = tumblr_api.create_post(
                blogname=BLOGNAME,
                content=t.content,
                tags=["hp.automated", "hp.twitter"],
                media_sources=media_sources,
            )

            logging.debug("[Tumblr] {}".format(response))

            for filename in filenames:
                os.remove(filename)
        else:
            logging.warning("[Tumblr] unrecognised HopperTask")


async def main() -> None:

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    queue: Queue[HopperTask] = Queue()

    twitter_task = setup_twitter(queue)
    tumblr_task = setup_tumblr(queue)

    printing_task = asyncio.create_task(printing())

    await printing_task
    await twitter_task
    await tumblr_task


if __name__ == "__main__":
    asyncio.run(main())
