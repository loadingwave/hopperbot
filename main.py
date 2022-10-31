import asyncio
import logging

from tweepy import StreamRule

from hopperbot.secrets import twitter_keys
from hopperbot.twitter import TwitterListener


async def printing() -> None:
    for i in range(50):
        print("[Printing] ", i)
        await asyncio.sleep(5)


async def main() -> None:

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    twitter_client = TwitterListener(**twitter_keys)

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

    # This is a Task
    twitter_task = twitter_client.filter(
        expansions=expansions, media_fields=media_fields
    )

    printing_task = asyncio.create_task(printing())

    await printing_task
    await twitter_task


if __name__ == "__main__":
    asyncio.run(main())
