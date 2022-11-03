import logging
import os
import sqlite3 as sqlite
from asyncio import Queue
from typing import List, Tuple, Union

from tweepy import ReferencedTweet, Response, Tweet
from tweepy.asynchronous import AsyncClient as TwitterApi
from tweepy.asynchronous import AsyncStreamingClient

from hopperbot.debug import twitter_data, twitter_updatables
from hopperbot.hoppertasks import ContentBlock, TumblrPost, Update
from hopperbot.people import NONE, Person
from hopperbot.renderer import Renderer


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


def query_tweet_db(tweet_id: int) -> Union[None, Tuple[int, int, str]]:
    tweets_db = sqlite.connect("tweets.db", detect_types=sqlite.PARSE_DECLTYPES)

    result = None

    with tweets_db:
        cur = tweets_db.execute("SELECT tweet_index, reblog_id, blogname FROM tweets WHERE tweet_id = ?", [tweet_id])
        response = cur.fetchone()
        if response is None:
            result = None
        else:
            (tweet_index, reblog_id, blogname) = response
            result = (tweet_index, reblog_id, blogname)

    tweets_db.close()

    return result


async def get_thread(
    twitter_token: str, tweet: Tweet, username: str
) -> Tuple[List[str], List[int], int, int, Union[None, Tuple[int, str]]]:
    alt_texts = [f"Tweet by @{username}: {tweet.text}"]
    replied_to: List[int] = []

    if tweet.in_reply_to_user_id is not None:

        api = TwitterApi(bearer_token=twitter_token)

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
                (tweet_index, tumblr_id, blog_name) = result
                alt_texts.reverse()
                replied_to.reverse()
                return (alt_texts, replied_to, tweet_index + len(alt_texts), len(alt_texts), (tumblr_id, blog_name))

            expansions = [
                "author_id",
                "in_reply_to_user_id",
                "attachments.media_keys",
                "referenced_tweets.id",
            ]

            # Get next tweet
            response = await api.get_tweet(id=referenced.id, expansions=expansions)

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


class TwitterUpdate(Update):

    filenames: Union[None, List[str]] = None
    tweet_index: Union[None, int] = None

    def __init__(
        self,
        username: str,
        tweet: Tweet,
    ) -> None:
        self.username = username
        self.tweet = tweet
        super().__init__()

    # Using "type: ignore" for **kwargs
    async def process(self, renderer: Renderer, twitter_token: str, **kwargs) -> TumblrPost:  # type: ignore
        content: List[ContentBlock] = [{}]
        (alt_texts, conversation, tweet_index, thread_height, reblog) = await get_thread(
            twitter_token, self.tweet, self.username
        )

        self.tweet_index = tweet_index

        content = [header_block(self.tweet.author_id, conversation)]

        url = f"https://twitter.com/{self.username}/status/{self.tweet.id}"

        # Building update
        if not alt_texts:
            logging.error("[Twitter] Zero alt texts found (this should be impossible :/)")
        else:
            last = alt_texts.pop()
            last_block = tweet_block(f"tweet{len(alt_texts)}", last, url)

            for (i, alt_text) in enumerate(alt_texts):
                block = tweet_block(f"tweet{i}", alt_text)
                content.append(block)

            content.append(last_block)

        filename_prefix = str(self)
        filenames = renderer.render_tweets(url, filename_prefix, tweet_index, thread_height)
        self.filenames = filenames

        media_sources = {f"tweet{i}": filename for (i, filename) in enumerate(filenames)}

        post = TumblrPost(
            twitter_updatables[self.username], content, ["hb.automated", "hb.twitter"], media_sources, reblog
        )

        return post

    def cleanup(self) -> None:
        if self.filenames:
            for filename in self.filenames:
                os.remove(filename)
        else:
            logging.warning("[Twitter] TwitterUpdate did not have any filenames to delete")

    def __str__(self) -> str:
        return "tweet" + str(self.tweet.id)


class TwitterListener(AsyncStreamingClient):
    def __init__(self, queue: Queue[Update], bearer_token: str) -> None:
        self.queue = queue

        # To be able to follow reblog trails, we need to be able to lookup tweets
        super().__init__(bearer_token)

    async def on_connect(self) -> None:
        logging.info("[Twitter] Listener is connected")

    async def reset_rules(self) -> None:
        get_response = await self.get_rules()
        print(get_response)
        if isinstance(get_response, Response):
            (data, _, errors, _) = get_response
            if errors:
                for error in errors:
                    logging.error(f'[Twitter] Trying to get rules returned an error: "{error}"')
            elif data:
                delete_response = await self.delete_rules(data)
                if isinstance(delete_response, Response):
                    if errors:
                        for error in errors:
                            logging.error(f'[Twitter] Trying to delete rules returned an error: "{error}"')
                else:
                    logging.error("[Twitter] Trying to delete rules did not return a Response somehow")
        else:
            logging.error("[Twitter] Trying to get rules did not return a Response somehow")

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

        update = TwitterUpdate(username, tweet)

        await self.queue.put(update)
        logging.info(f'[Twitter] produced task: "{str(update)}: {tweet.text}"')
