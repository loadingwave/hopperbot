import asyncio
import logging
from asyncio import Queue
from typing import TypeAlias, Union, List

from tweepy import StreamRule
from tweepy.asynchronous import AsyncClient as TwitterApi
from pytumblr2 import TumblrRestClient as TumblrApi

from hopperbot.secrets import twitter_keys, tumblr_keys
from hopperbot.twitter import TwitterListener
from hopperbot.renderer import Renderer

ContentBlock: TypeAlias = dict[str, Union[str, dict[str, str], List[dict[str, str]]]]


class HopperTask:
    def __init__(self, content: List[ContentBlock]) -> None:
        self.content = content


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
    print(tumblr_api, renderer)


async def main() -> None:

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    queue: Queue[HopperTask] = Queue()

    twitter_task = setup_twitter(queue)

    printing_task = asyncio.create_task(printing())

    await printing_task
    await twitter_task


if __name__ == "__main__":
    asyncio.run(main())
