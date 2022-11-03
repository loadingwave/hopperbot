import logging
from asyncio import Queue
from typing import List, Tuple, Union
import sqlite3 as sqlite

from tweepy import Response, Tweet, ReferencedTweet
from tweepy.asynchronous import AsyncClient, AsyncStreamingClient

from hopperbot.config import twitter_data
from hopperbot.hoppertasks import ContentBlock, Update
from hopperbot.people import NONE, Person


class TwitterUpdate(Update):
    def __init__(
        self,
        content: List[ContentBlock],
        url: str,
        identifier: int,
        tweet_index: int,
        thread_height: int,
        reblog_key: Union[None, int],
    ) -> None:
        self.url = url
        self.tweet_index = tweet_index
        self.thread_height = thread_height
        super().__init__(content, identifier, reblog_key)


def header_block(user_id: int, replied_to: List[int] = []) -> ContentBlock:
    if user_id in twitter_data:
        person = twitter_data[user_id]
    else:
        # This situation should never happen, but the code does not prevent it from happening,
        # so its better to add in a check for it in my opinion
        person = Person("someone", [NONE])

    if replied_to:
        people = {twitter_data[id].name for id in replied_to if id in twitter_data}

        if person.name in people:
            people.remove(person.name)
            people.add(person.emself())

        others = sum(set(map(lambda id: (id not in twitter_data), replied_to)))

        if people:
            if others >= 2:
                replies = ", ".join(people) + " and some others"
            elif others == 1:
                replies = ", ".join(people) + " and someone else"
            elif len(people) == 1:
                replies = people.pop()
            else:
                # people has at least 2 elements, because it isn't falsy and its length is not 1
                last = people.pop()
                replies = ", ".join(people) + " and " + last
        else:
            if others >= 2:
                replies = "some people"
            elif others == 1:
                replies = "someone"
            else:
                # This situation should never happen, but again, better to add in a check for it
                replies = "no one"

        return {"type": "text", "text": f"{person.name} replied to {replies} on Twitter!"}
    else:
        return {
            "type": "text",
            "text": f"{person.name} posted on Twitter!",
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


def query_tweet_db(tweet_id: int) -> Union[None, Tuple[int, int]]:
    tweets_db = sqlite.connect("tweets.db", detect_types=sqlite.PARSE_DECLTYPES)

    result = None

    with tweets_db:
        cur = tweets_db.execute("SELECT tweet_id, reblog_key, thread_index FROM tweets WHERE tweet_id = ?", [tweet_id])
        response = cur.fetchone()
        if response is None:
            result = None
        else:
            (_, reblog_key, thread_index) = response
            result = (reblog_key, thread_index)

    tweets_db.close()

    return result


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

        url = f"https://twitter.com/{username}/status/{tweet.id}"

        # Processing information
        (alt_texts, conversation, tweet_index, thread_height, reblog_key) = await self.get_thread(tweet, username)

        content = [header_block(author.id, conversation)]

        # Building update
        if not alt_texts:
            logging.error("[Twitter] Zero alt texts found (this should be impossible :/)")
            return

        last = alt_texts.pop()
        last_block = tweet_block(f"tweet{len(alt_texts)}", last, url)

        for (i, alt_text) in enumerate(alt_texts):
            block = tweet_block(f"tweet{i}", alt_text)
            content.append(block)

        content.append(last_block)

        update = TwitterUpdate(content, url, tweet.id, tweet_index, thread_height, reblog_key)

        await self.queue.put(update)
        logging.info(f'[Twitter] produced task: "tweet{update.identifier}: {tweet.text}"')

    async def get_thread(self, tweet: Tweet, username: str) -> Tuple[List[str], List[int], int, int, Union[int, None]]:
        alt_texts = [f"Tweet by @{username}: {tweet.text}"]
        replied_to: List[int] = []

        current_tweet = tweet

        while current_tweet.in_reply_to_user_id is not None:
            replied_to.append(current_tweet.in_reply_to_user_id)

            # Prepare tweet request
            if not current_tweet.referenced_tweets:
                break

            referenced: Union[None, ReferencedTweet] = next(
                filter(lambda t: t.type == "replied_to", current_tweet.referenced_tweets)
            )
            if referenced is None:
                break

            result = query_tweet_db(referenced.id)
            if result is not None:
                (reblog_key, thread_index) = result
                alt_texts.reverse()
                replied_to.reverse()
                return (alt_texts, replied_to, thread_index + len(alt_texts), len(alt_texts), reblog_key)

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

        return (alt_texts, replied_to, len(alt_texts), len(alt_texts), None)
