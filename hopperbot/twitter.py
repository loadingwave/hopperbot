from tweepy.asynchronous import AsyncStreamingClient, AsyncClient
from tweepy import Response, Tweet
import logging
from asyncio import Queue, run
from typing import Tuple, List


class TwitterListener(AsyncStreamingClient):
    def __init__(self, queue: Queue[str], api: AsyncClient, bearer_token: str) -> None:
        self.queue = queue
        self.api = api
        super().__init__(bearer_token)

    async def on_connect(self) -> None:
        logging.info("TwitterListener is connected")

    async def on_response(self, response: Response) -> None:
        tweet: Tweet
        (tweet, includes, errors, _) = response
        if errors:
            for error in errors:
                logging.error(error)
        else:
            logging.error("Not implemented")

    async def get_thread(
        self, tweet: Tweet, username: str
    ) -> Tuple[List[str], List[int], int]:
        alt_texts = ["Tweet by @{}: {}".format(username, tweet.text)]
        replied_to: List[int] = []
        thread_depth = 1

        current_tweet = tweet
        while current_tweet.in_reply_to_user_id is not None:
            replied_to.append(current_tweet.in_reply_to_user_id)
            thread_depth += 1

            # Prepare tweet request
            referenced = next(
                filter(
                    lambda t: t.type == "replied_to", current_tweet.referenced_tweets
                )
            )
            if not referenced:
                break

            expansions = [
                "author_id",
                "in_reply_to_user_id",
                "attachments.media_keys",
                "referenced_tweets.id",
            ]

            # Get next tweet
            response = await run(
                self.api.get_tweet(id=referenced.id, expansions=expansions)
            )
            if not isinstance(response, Response):
                logging.error(
                    "Twitter API did not return a response while retrieving tweet {}".format(
                        referenced.id
                    )
                )
                break

            (ref_tweet, ref_includes, ref_errors, _) = response
            if ref_errors:
                for error in ref_errors:
                    logging.error(error)
                break

            ref_author = ref_includes["users"][0]
            alt_texts.append(
                "Tweet by @{}: {}".format(ref_author["username"], ref_tweet.text)
            )
            current_tweet = ref_tweet

        return (alt_texts, replied_to, thread_depth)
