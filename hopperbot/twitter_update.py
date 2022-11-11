import logging
import os
from typing import Optional, Tuple, Union

from tweepy import ReferencedTweet, Response, Tweet
from tweepy.asynchronous import AsyncClient as TwitterApi

from hopperbot.config import TWITTER_BLOGNAMES
from hopperbot.database import database as db
from hopperbot.renderer import RENDERER
from hopperbot.secrets import twitter_keys
from hopperbot.tumblr import TumblrPost, Update, image_block, text_block

logger = logging.getLogger("Twitter")
logger.setLevel(logging.DEBUG)


def header_text(user_id: int, conversation: set[int] = set()) -> str:
    person = db.get_person(user_id)
    if person is None:
        logger.error(f"Author id {user_id} was not found in twitter data")
        return "Something went wrong with the bot and no header text could be generated :("

    if conversation:
        possible_people = [db.get_person(id) for id in conversation]
        # Note that people is using {} not [], so it is a set, meaning every name can only appear once
        people = {person.name for person in possible_people if person is not None}

        if person.name in people:
            people.remove(person.name)
            people.add(person.emself())

        others = len([1 for person in possible_people if person is None])

        if people:
            last = " and some others " if others > 1 else (" and someone else" if others == 1 else people.pop())
            rest = ", ".join(people) + "and " if people else ""
            replies = rest + last
        else:
            replies = "someone" if others == 1 else "some people"

        return f"{person.name} replied to {replies} on Twitter!"
    else:
        return f"{person.name} posted on Twitter!"


async def get_thread(tweet: Tweet, username: str) -> Tuple[list[str], list[int], range, Optional[Tuple[int, str]]]:
    alt_texts = [f"Tweet by @{username}: {tweet.text}"]
    conversation: list[int] = []

    if tweet.in_reply_to_user_id is not None:

        logger.debug(f"Fetching thread for tweet {tweet.id}")

        api = TwitterApi(**twitter_keys)

        curr_tweet = tweet
        while curr_tweet.in_reply_to_user_id is not None:

            conversation.append(curr_tweet.in_reply_to_user_id)

            # Prepare tweet request
            if not curr_tweet.referenced_tweets:
                logger.error(f"in_reply_to_user_id is set for tweet {curr_tweet.id}, but no referenced_tweets exist")
                break

            ref_tweet: Union[None, ReferencedTweet] = next(
                filter(lambda t: t.type == "replied_to", curr_tweet.referenced_tweets)
            )
            if ref_tweet is None:
                logger.error(f"in_reply_to_user_id is set for tweet {curr_tweet.id}, but no referenced_tweets exist")
                break

            result = db.get_tweet(ref_tweet.id)
            if result is not None:
                (tweet_index, tumblr_id, blog_name) = result
                alt_texts.reverse()
                conversation.reverse()

                thread_range = range(tweet_index, tweet_index + len(alt_texts))
                return (alt_texts, conversation, thread_range, (tumblr_id, blog_name))

            expansions = ["author_id", "in_reply_to_user_id", "referenced_tweets.id"]

            # Get next tweet
            response = await api.get_tweet(id=ref_tweet.id, expansions=expansions)

            if not isinstance(response, Response):
                logger.error(f"API did not return a Response while fetching tweet {ref_tweet.id}")
                break

            # This is a little white lie, but it is correct in the case of "users"
            ref_includes: dict[str, dict[str, str]]

            next_tweet: Tweet
            (next_tweet, ref_includes, ref_errors, _) = response
            if ref_errors:
                for error in ref_errors:
                    logger.error(f"Error while fetching tweet {ref_tweet.id}: {error}")
                break

            ref_author = ref_includes.get("users")
            if ref_author is None:
                logger.error(f"API did not return users while fetching tweet {ref_tweet.id}")
                break
            alt_texts.append(f'Tweet by @{ref_author.get("username")}: {curr_tweet.text}')

            curr_tweet = next_tweet

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

        (alt_texts, conversation, thread_range, reblog) = await get_thread(self.tweet, self.username)
        logger.debug(f"Got thread for update {str(self)}")

        content = [text_block(header_text(self.tweet.author_id, set(conversation)))]

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

        blogname = TWITTER_BLOGNAMES.get(self.username.lower())
        if blogname is None:
            logger.error(f"No blogname found for {self.username}")
            blogname = "test37"
        else:
            logger.debug(f"Going to post tweet {self.tweet.id} from {self.username} to {blogname}")

        post = TumblrPost(blogname, content, ["hb.automated", "hb.twitter"], media_sources, reblog)

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
            blogname = TWITTER_BLOGNAMES.get(self.username.lower())
            if blogname is None:
                logger.error(f"No blogname found for username {self.username}")
            else:
                db.add_tweet(self.tweet.id, self.tweet_index, tumblr_id, blogname)

    def __str__(self) -> str:
        return "tweet" + str(self.tweet.id)