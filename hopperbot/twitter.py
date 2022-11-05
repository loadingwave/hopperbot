import logging
import os
from asyncio import Queue
from typing import Optional, Tuple, Union

from tweepy import ReferencedTweet, Response, StreamRule, Tweet
from tweepy.asynchronous import AsyncClient as TwitterApi
from tweepy.asynchronous import AsyncStreamingClient

import hopperbot.database as db
from hopperbot.config import twitter_data, twitter_updatables
from hopperbot.renderer import RENDERER
from hopperbot.tumblr import ContentBlock, TumblrPost, Update, image_block, text_block
from hopperbot.secrets import twitter_keys

tweepy_logger = logging.getLogger("tweepy")
tweepy_logger.setLevel(logging.INFO)

logger = logging.getLogger("Twitter")

TWITTER_RULE_MAX_LEN = 512


def header_text(user_id: int, conversation: list[int] = []) -> str:
    person = twitter_data.get(user_id)
    if person is None:
        logger.error(f"Author id {user_id} was not found in twitter data")
        return "Something went wrong with the bot and no header text could be generated :("

    if conversation:
        people = {twitter_data[id].name for id in conversation if id in twitter_data}

        if person.name in people:
            people.remove(person.name)
            people.add(person.emself())

        others = sum(set(map(lambda id: (id not in twitter_data), conversation)))

        if people:
            last = " and some others " if others > 1 else (" and someone else" if others == 1 else people.pop())
            rest = ", ".join(people) + "and " if people else ""
            replies = rest + last
        else:
            replies = "someone" if others == 1 else "some people"

        return f"{person.name} replied to {replies} on Twitter!"
    else:
        return f"{person.name} posted on Twitter!"


async def get_thread(tweet: Tweet, username: str) -> Tuple[list[str], list[int], range, Union[None, Tuple[int, str]]]:
    alt_texts = [f"Tweet by @{username}: {tweet.text}"]
    conversation: list[int] = []

    if tweet.in_reply_to_user_id is not None:

        api = TwitterApi(**twitter_keys)

        curr_tweet = tweet
        while curr_tweet.in_reply_to_user_id is not None:
            conversation.append(curr_tweet.in_reply_to_user_id)

            # Prepare tweet request
            if not curr_tweet.referenced_tweets:
                break

            next_tweet: Union[None, ReferencedTweet] = next(
                filter(lambda t: t.type == "replied_to", curr_tweet.referenced_tweets)
            )
            if next_tweet is None:
                break

            result = db.get_tweet(next_tweet.id)
            if result is not None:
                (tweet_index, tumblr_id, blog_name) = result
                alt_texts.reverse()
                conversation.reverse()

                thread_range = range(tweet_index, tweet_index + len(alt_texts))
                return (alt_texts, conversation, thread_range, (tumblr_id, blog_name))

            expansions = ["author_id", "in_reply_to_user_id", "referenced_tweets.id"]

            # Get next tweet
            response = await api.get_tweet(id=next_tweet.id, expansions=expansions)

            if not isinstance(response, Response):
                logger.error(f"API did not return a Response while fetching tweet {next_tweet.id}")
                break

            # This is a little white lie, but it is correct in the case of "users"
            ref_includes: dict[str, dict[str, str]]

            (curr_tweet, ref_includes, ref_errors, _) = response
            if ref_errors:
                for error in ref_errors:
                    logger.error(f"Error while fetching tweet {next_tweet.id}: {error}")
                break

            ref_author = ref_includes.get("users")
            if ref_author is None:
                logger.error(f"API did not return users while fetching tweet {next_tweet.id}")
                break
            alt_texts.append(f'Tweet by @{ref_author.get("username")}: {curr_tweet.text}')

    alt_texts.reverse()
    conversation.reverse()

    return (alt_texts, conversation, range(len(alt_texts)), None)


class TwitterUpdate(Update):

    filenames: Optional[list[str]] = None
    tweet_index: Optional[int] = None

    def __init__(self, username: str, tweet: Tweet) -> None:
        self.username = username
        self.tweet = tweet
        super().__init__()

    async def process(self) -> TumblrPost:
        content: list[ContentBlock] = [{}]
        (alt_texts, conversation, thread_range, reblog) = await get_thread(self.tweet, self.username)

        content = [text_block(header_text(self.tweet.author_id, conversation))]

        url = f"https://twitter.com/{self.username}/status/{self.tweet.id}"

        # Building update
        if not alt_texts:
            logger.error("Zero alt texts found (this should be impossible :/)")
        else:
            for (i, alt_text) in enumerate(alt_texts):
                if i == len(alt_texts):
                    block = image_block(f"tweet{i}", alt_text, url)
                else:
                    block = image_block(f"tweet{i}", alt_text)
                content.append(block)

        filename_prefix = str(self)
        filenames = RENDERER.render_tweets(url, filename_prefix, thread_range)
        self.filenames = filenames

        media_sources = {f"tweet{i}": filename for (i, filename) in enumerate(filenames)}

        post = TumblrPost(
            twitter_updatables[self.username], content, ["hb.automated", "hb.twitter"], media_sources, reblog
        )

        self.tweet_index = thread_range.stop
        return post

    def cleanup(self, tumblr_id: int) -> None:
        if self.filenames:
            for filename in self.filenames:
                os.remove(filename)
        else:
            logger.warning("TwitterUpdate did not have any filenames to delete")

        if self.tweet_index is None:
            logger.error("tweet_index is not set, tumblr post not added to the database")
        else:
            db.add_tweet(self.tweet.id, self.tweet_index, tumblr_id, twitter_updatables[self.username])

    def __str__(self) -> str:
        return "tweet" + str(self.tweet.id)


class TwitterListener(AsyncStreamingClient):
    def __init__(self, queue: Queue[Update], bearer_token: str) -> None:
        self.queue = queue

        # To be able to follow reblog trails, we need to be able to lookup tweets
        super().__init__(bearer_token)

    async def on_connect(self) -> None:
        logger.info("Twitter Listener is connected")

    async def reset_rules(self) -> None:
        get_response = await self.get_rules()
        if isinstance(get_response, Response):
            data: list[StreamRule]
            (data, _, errors, _) = get_response
            if errors:
                for error in errors:
                    logger.error(f'Trying to get rules returned an error: "{error}"')
            elif data:
                delete_response = await self.delete_rules(data)
                if isinstance(delete_response, Response):
                    if errors:
                        for error in errors:
                            logger.error(f'Trying to delete rules returned an error: "{error}"')
                    else:
                        for rule in data:
                            logger.debug(f'Deleted rule: "{rule.value}"')
                else:
                    logger.error("Trying to delete rules did not return a Response somehow")
        else:
            logger.error("Trying to get rules did not return a Response somehow")

    async def on_response(self, response: Response) -> None:
        tweet: Tweet
        # This is a little while lie, but it is correct when fetching a username
        includes: dict[str, list[dict[str, str]]]
        (tweet, includes, errors, _) = response
        if errors:
            for error in errors:
                logger.error(f"Got send a response, but it contained errors: {error}")
            return

        users = includes.get("users")
        if users is None:
            logger.error("Got send a response, but it did not contain users")
            return

        username = users[0].get("username")
        if username is None:
            logger.error("Got send a response, but first included user did not have a username")
            return

        update = TwitterUpdate(username, tweet)

        await self.queue.put(update)
        logger.info(f'Produced update: "{str(update)}: {tweet.text}"')

    async def add_usernames(self, usernames: list[str]) -> None:
        if len(usernames) <= 21:
            rule = StreamRule(" OR ".join(map(lambda x: "from:" + x, usernames)), "rule0")
            response = await self.add_rules(rule)
            if isinstance(response, Response):
                for added_rule in response.data:
                    logger.debug(f'Added rule: "{added_rule.value}"')
            else:
                logger.error("Adding rules did not return a Response somehow")
        else:
            next = usernames.pop()

            # Generate at most 5 rules with as many usernames as possible per rule
            for i in range(5):
                rule = "from:" + next
                next = usernames.pop()

                while next is not None and len(rule) + 9 + len(next) <= TWITTER_RULE_MAX_LEN:
                    rule += " OR from:" + next
                    next = usernames.pop()

                streamrule = StreamRule(rule, f"rule{i}")

                response = await self.add_rules(streamrule)

                if isinstance(response, Response):
                    for added_rule in response.data:
                        logger.debug(f'Added rule: "{added_rule.value}"')
                else:
                    logger.error("Adding rules did not return a Response somehow")

                if next is None:
                    # if there are no more users to add, stop generating rules
                    break

            if len(usernames) > 0:
                logger.error(f"{len(usernames)} usernames did not fit in a rule, so were not added")
