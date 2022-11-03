from hopperbot.twitter import TwitterListener
from hopperbot.secrets import twitter_keys
from asyncio import Queue, run
from hopperbot.hoppertasks import Update


async def main() -> None:
    queue: Queue[Update] = Queue()
    twitter_client = TwitterListener(queue=queue, **twitter_keys)

    await twitter_client.reset_rules()


if __name__ == "__main__":
    run(main())
