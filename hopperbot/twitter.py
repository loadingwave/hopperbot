import logging
import random
from asyncio import Queue
from typing import List, Tuple, TypeAlias, Union

from tweepy import Response, Tweet
from tweepy.asynchronous import AsyncClient, AsyncStreamingClient

from hopperbot.config import twitter_names
from hopperbot.hoppertasks import HopperTask, TwitterTask

ContentBlock: TypeAlias = dict[str, Union[str, dict[str, str], List[dict[str, str]]]]


class TwitterListener(AsyncStreamingClient):
    def __init__(
        self, queue: Queue[HopperTask], api: AsyncClient, bearer_token: str
    ) -> None:
        self.queue = queue
        self.api = api
        super().__init__(bearer_token)

    async def on_connect(self) -> None:
        print("listener is connectred")
        logging.info("[Twitter] Listener is connected")

    async def on_response(self, response: Response) -> None:
        tweet: Tweet
        (tweet, includes, errors, _) = response
        if errors:
            for error in errors:
                logging.error(error)
            return
        logging.info("[Twitter] {}".format(tweet))
        author = includes["users"][0]
        username = author["username"]

        (alt_texts, conversation, thread_depth) = await self.get_thread(tweet, username)

        identifier = "tweet{}".format(tweet.id)
        url = "https://twitter.com/{}/status/{}".format(username, tweet.id)

        content = [self.header_block(author.id, conversation)]

        for (i, alt_text) in enumerate(reversed(alt_texts)):
            if i == thread_depth:
                block = self.tweet_block("tweet{}".format(i), alt_text, url)
            else:
                block = self.tweet_block("tweet{}".format(i), alt_text)

            content.append(block)

        task = TwitterTask(content, url, identifier, thread_depth, thread_depth)

        logging.info("[Twitter] Queued tweet")
        await self.queue.put(task)

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
            response = await self.api.get_tweet(id=referenced.id, expansions=expansions)

            if not isinstance(response, Response):
                logging.error(
                    "[Twitter] API did not return a response while retrieving tweet {}".format(
                        referenced.id
                    )
                )
                break

            (ref_tweet, ref_includes, ref_errors, _) = response
            if ref_errors:
                for error in ref_errors:
                    logging.error("[Twitter] {}".format(error))
                break

            ref_author = ref_includes["users"][0]
            alt_texts.append(
                "Tweet by @{}: {}".format(ref_author["username"], ref_tweet.text)
            )
            current_tweet = ref_tweet

        return (alt_texts, replied_to, thread_depth)

    def header_block(self, user_id: int, replied_to: List[int] = []) -> ContentBlock:
        (name, pronouns) = twitter_names[user_id]
        if replied_to:
            people = {
                twitter_names.get(i, "someone")[0]
                for i in replied_to
                if i in twitter_names
            }

            if name in people:
                people.remove(name)
                people.add(random.choice(pronouns))

            others = {i for i in replied_to if i not in twitter_names}

            people_count = len(people)
            people_iter = iter(people)

            replies = next(people_iter)
            people_count -= 1

            while people_count > 1 or (people_count == 1 and len(others) != 0):
                replies += ", " + next(people_iter)
                people_count -= 1

            if len(others) >= 2:
                replies += " and some others"
            elif len(others) == 1:
                replies += " and someone else"
            elif people_count > 0:
                replies += " and {}".format(next(people_iter))

            return {
                "type": "text",
                "text": "{} replied to {} on Twitter!".format(name, replies),
            }
        else:
            return {
                "type": "text",
                "text": "{} posted on Twitter!".format(name),
            }

    def tweet_block(
        self, identifier: str, alt_text: str, url: Union[str, None] = None
    ) -> ContentBlock:
        block: ContentBlock = {
            "type": "image",
            "media": [
                {
                    "type": "image/png",
                    "identifier": identifier,
                }
            ],
            "alt_text": alt_text,
        }

        if url is None:
            return block
        else:
            block["attribution"] = {
                "type": "app",
                "url": url,
                "app_name": "Twitter",
                "display_text": "View on Twitter",
            }
            return block
