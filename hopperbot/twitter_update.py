import logging
from typing import Optional, Tuple, Union, cast, Any

from tweepy import ReferencedTweet, Response, Tweet, User
from tweepy.asynchronous import AsyncClient as TwitterApi

# from hopperbot.config import TWITTER_BLOGNAMES
from hopperbot.database import database as db
from hopperbot.renderer import Renderer
from hopperbot.secrets import twitter_keys
from hopperbot.tumblr import TumblrPost, Renderable

logger = logging.getLogger("Twitter")
logger.setLevel(logging.DEBUG)


class TwitterException(Exception):
    pass


class TweetNotFound(TwitterException):
    pass


class NoReferencedTweet(TwitterException):
    pass


class InvalidTwitterResponse(TwitterException):
    pass


class TwitterRenderable(Renderable):
    def __init__(self, url: str, thread_range: range, ids: list[str], filename_prefix: str) -> None:
        self.url = url
        if len(thread_range) != len(ids):
            raise ValueError("Thread range and number of ids should be equal")
        self.thread_range = thread_range
        self.ids = ids
        self.filename_prefix = filename_prefix

    def render(self, renderer: Renderer) -> dict[str, str]:
        filenames = renderer.render_tweets(self.url, self.filename_prefix, self.thread_range)
        return {id : filename for (id, filename) in zip(self.ids, filenames)}


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


class TwitterUpdate(TumblrPost):

    thread_range: range
    alt_texts: list[str]
    conversation: list[int]

    def __init__(self, username: str, tweet: Tweet) -> None:
        self.username = username
        self.tweet = tweet
        self.alt_texts = [tweet.text]
        self.conversation = [tweet.author_id]
        author = db.get_person(tweet.author_id)
        if author is None:
            logging.warning(f"Captured tweet from unknown twitter account ({tweet.author_id})")
            self.add_text_block("Someone posted on twitter!")
        else:
            self.add_text_block(f"{author.name.capitalize()} posted on twitter!")
        super().__init__()

    def get_replyee(self, tweet: Tweet) -> Optional[int]:
        """Gets the id of the tweet the supplied tweet was replying to. Returns
        None if the tweet didn't reply to anyone. If such a tweet should exist
        but doesnt, the function throws a NoReferencedTweet exeption"""
        if not tweet.in_reply_to_user_id:
            return None

        if not tweet.referenced_tweets:
            logger.error(f"in_reply_to_user_id is set for tweet {tweet.id}, but no referenced_tweets exist")
            raise NoReferencedTweet

        ref_tweet = next(filter(lambda t: t.type == "replied_to", tweet.referenced_tweets))
        ref_tweet = cast(ReferencedTweet, ref_tweet)
        if ref_tweet is None:
            logger.error(f"in_reply_to_user_id is set for tweet {tweet.id}, but no referenced_tweets exist")
            raise NoReferencedTweet

        return ref_tweet.id

    async def fetch_and_process_tweet(self, tweet_id: int, api: TwitterApi) -> Tweet:
        """Gets and returns the tweet in question and updates the conversation and alt texts
        Raises a TwitterException if anything goes wrong
        """
        # Fetch tweet:
        expansions = ["author_id", "in_reply_to_user_id", "referenced_tweets.id"]
        response = await api.get_tweet(id=tweet_id, expansions=expansions)

        # Error handling:
        if not isinstance(response, Response):
            logger.error(f"API did not return a Response while fetching tweet {tweet_id}")
            raise TwitterException

        includes: dict[str, Any]
        tweet: Tweet
        (tweet, includes, errors, _) = response
        if errors:
            for error in errors:
                logger.error(f"Error while fetching tweet {tweet_id}: {error}")
            raise TwitterException

        users = includes.get("users")
        if not users:
            # This condition filters both for None and an empty list
            logger.error(f"API did not return users while fetching tweet {tweet_id}")
            raise TwitterException
        users = cast(list[User], users)

        author = users[0]

        # Process the data that is not contained in the Tweet class:
        self.alt_texts.append(f'Tweet by @{author.username}: {tweet.text}')
        self.conversation.append(author.id)

        return tweet

    async def fetch_thread(self):
        if not self.tweet.in_reply_to_user_id:
            return
        # api = TwitterApi(**twitter_keys)
        pass
