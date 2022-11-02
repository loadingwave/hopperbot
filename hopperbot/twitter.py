import logging
import random
from asyncio import Queue
from typing import List, Tuple, Union

from tweepy import Response, Tweet
from tweepy.asynchronous import AsyncClient, AsyncStreamingClient

from hopperbot.config import twitter_data
from hopperbot.hoppertasks import ContentBlock, Update


class TwitterUpdate(Update):
    def __init__(
        self,
        content: List[ContentBlock],
        url: str,
        identifier: str,
        tweet_index: int,
        thread_height: int,
    ) -> None:
        self.url = url
        self.tweet_index = tweet_index
        self.thread_height = thread_height
        super().__init__(content, identifier)


def header_block(user_id: int, replied_to: List[int] = []) -> ContentBlock:
    if user_id in twitter_data:
        (name, pronouns) = twitter_data[user_id]
    else:
        # This situation should never happen, but the code does not prevent it from happening, so its better
        # to add in a check for it in my opinion
        name = "Someone"
        pronouns = ["themself"]

    if replied_to:
        # We can safely use twitter_data[i] because we check if i is in twitter_data
        people = {twitter_data[i][0] for i in replied_to if i in twitter_data}

        if name in people:
            people.remove(name)
            # pronouns should never be empty, but better safe then sorry
            if pronouns:
                people.add(random.choice(pronouns))
            else:
                people.add("themself")

        # These set operations are not the most efficient, but their size is very small, so it should be okay
        others = {i for i in replied_to if i not in twitter_data}

        if people:
            if len(others) >= 2:
                replies = ", ".join(people) + " and some others"
            elif len(others) == 1:
                replies = ", ".join(people) + " and someone else"
            elif len(people) == 1:
                replies = people.pop()
            else:
                # people has at least 2 elements, because it isn't falsy and its length is not 1
                last = people.pop()
                replies = ", ".join(people) + " and " + last
        else:
            if len(others) >= 2:
                replies = "some people"
            elif len(others) == 1:
                replies = "someone"
            else:
                # This situation should never happen, but again, better to add in a check for it
                replies = "no one"

        return {"type": "text", "text": f"{name} replied to {replies} on Twitter!"}
    else:
        return {
            "type": "text",
            "text": f"{name} posted on Twitter!",
        }


def tweet_block(identifier: str, alt_text: str, url: Union[str, None] = None) -> ContentBlock:
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


class TwitterListener(AsyncStreamingClient):
    def __init__(self, queue: Queue[Update], api: AsyncClient, bearer_token: str) -> None:
        self.queue = queue

        # To be able to follow reblog trails, we need to be able to lookup tweets
        self.api = api
        super().__init__(bearer_token)

    async def on_connect(self) -> None:
        logging.info("[Twitter] Listener is connected")

    async def on_response(self, response: Response) -> None:
        tweet: Tweet
        (tweet, includes, errors, _) = response
        if errors:
            for error in errors:
                logging.error(f"[Twitter] {error}")
            return

        # Extracting raw information
        logging.debug(f"[Twitter] {tweet}")
        author = includes["users"][0]
        username = author["username"]

        identifier = f"tweet{tweet.id}"
        url = f"https://twitter.com/{username}/status/{tweet.id}"

        # Processing information
        (alt_texts, conversation, thread_depth) = await self.get_thread(tweet, username)

        content = [header_block(author.id, conversation)]

        # Building update
        if not alt_texts:
            logging.error("[Twitter] Zero alt texts found (this should be impossible)")
            return

        last = alt_texts.pop()
        last_block = tweet_block(f"tweet{len(alt_texts)}", last, url)

        for (i, alt_text) in enumerate(alt_texts):
            block = tweet_block(f"tweet{i}", alt_text)
            content.append(block)

        content.append(last_block)

        update = TwitterUpdate(content, url, identifier, thread_depth, thread_depth)

        await self.queue.put(update)
        logging.info(f'[Twitter] produced task "{update.identifier}"')

    async def get_thread(self, tweet: Tweet, username: str) -> Tuple[List[str], List[int], int]:
        alt_texts = [f"Tweet by @{username}: {tweet.text}"]
        replied_to: List[int] = []

        current_tweet = tweet
        while current_tweet.in_reply_to_user_id is not None:
            replied_to.append(current_tweet.in_reply_to_user_id)

            # Prepare tweet request
            if not current_tweet.referenced_tweets:
                break

            referenced = next(filter(lambda t: t.type == "replied_to", current_tweet.referenced_tweets))
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
                logging.error(f"[Twitter] API did not return a response while fetching tweet {referenced.id}")
                break

            (ref_tweet, ref_includes, ref_errors, _) = response
            if ref_errors:
                for error in ref_errors:
                    logging.error(f"[Twitter] {error}")
                break

            ref_author = ref_includes["users"][0]
            alt_texts.append(f'Tweet by @{ref_author["username"]}: {ref_tweet.text}')
            current_tweet = ref_tweet

        alt_texts.reverse()
        replied_to.reverse()

        return (alt_texts, replied_to, len(alt_texts))
