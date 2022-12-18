import logging
from typing import Optional, cast, Any

from tweepy import ReferencedTweet, Response, Tweet, User
from tweepy.asynchronous import AsyncClient as TwitterApi

# from hopperbot.config import TWITTER_BLOGNAMES
from hopperbot.database import database as db
from hopperbot.renderer import Renderer
from hopperbot.secrets import twitter_keys
from hopperbot.tumblr import TumblrPost, Renderable, TumblrApi
from hopperbot.errors import TwitterError, NoReferencedTweetError

logger = logging.getLogger("Twitter")
logger.setLevel(logging.DEBUG)


class TwitterRenderable(Renderable):
    def __init__(self, url: str, ids: list[str], filename_prefix: str, thread: Optional[range] = None) -> None:
        if thread is None:
            if len(ids) != 1:
                raise ValueError("Thread range and number of ids should be equal")
        elif len(thread) != len(ids):
            raise ValueError("Thread range and number of ids should be equal")

        self.url = url
        self.thread = thread
        self.ids = ids
        self.filename_prefix = filename_prefix

    def render(self, renderer: Renderer) -> dict[str, str]:
        filenames = renderer.render_tweets(self.url, self.filename_prefix, self.thread)
        return {id : filename for (id, filename) in zip(self.ids, filenames)}


class TwitterUpdate(TumblrPost):

    thread: range = range(0, 1)
    alt_texts: list[str]
    conversation: set[int] = set()

    def __init__(self, username: str, tweet: Tweet) -> None:
        self.tweet = tweet
        self.alt_texts = [f'Tweet by @{username}: {tweet.text}']
        self.url = f"https://twitter.com/{username}/status/{tweet.id}"
        super().__init__()

    def add_tweet(self):
        image_id = f"image{len(self.content)}"
        renderable = TwitterRenderable(self.url, [image_id], f"tweet-{len(self.content)}-")

        self.renderables.append(renderable)
        self.add_image_block(image_id, self.alt_texts[0], self.url)

    def add_tweets(self):
        if not len(self.alt_texts) == len(self.thread):
            raise ValueError("All tweets should have an alt text")

        start = len(self.content)
        image_ids = [f"image{index}" for index in range(start, start + len(self.thread))]
        renderable = TwitterRenderable(self.url, image_ids, f"tweet-{str(start)}-", self.thread)
        self.renderables.append(renderable)

        last_image_id = image_ids.pop()
        last_alt_text = self.alt_texts.pop()

        for image_id, alt_text in zip(image_ids, self.alt_texts):
            self.add_image_block(image_id, alt_text)

        self.add_image_block(last_image_id, last_alt_text, self.url)

    def add_header(self) -> None:
        person = db.get_person(self.tweet.author_id)
        if person is None:
            logger.error(f"Author id {self.tweet.author_id} was not found in twitter data")
            self.add_text_block("Something went wrong with the bot and no header text could be generated :(")
            return

        if self.conversation:
            possible_people = [db.get_person(id) for id in self.conversation]
            # Note that people is using {} not [], so it is a set, meaning every name can only appear once
            people = {person.name for person in possible_people if person is not None}

            if person.name in people:
                people.remove(person.name)
                people.add(person.emself())

            others = len([1 for person in possible_people if person is None])

            if people:
                last = " and some others " if others > 1 else (" and someone else" if others == 1 else people.pop())
                rest = ", ".join(people) + "and " if people else ""
                replyees = rest + last
            else:
                replyees = "someone" if others == 1 else "some people"

            self.add_text_block(f"{person.name.capitalize()} replied to {replyees} on Twitter!")
        else:
            self.add_text_block(f"{person.name} posted on Twitter!")

    def get_replyee_id(self, tweet: Tweet) -> Optional[int]:
        """Gets the id of the tweet the supplied tweet was replying to. Returns
        None if the tweet didn't reply to anyone. If such a tweet should exist
        but doesnt, the function throws a NoReferencedTweet exeption"""
        if not tweet.in_reply_to_user_id:
            return None

        if not tweet.referenced_tweets:
            logger.error(f"in_reply_to_user_id is set for tweet {tweet.id}, but no referenced_tweets exist")
            raise NoReferencedTweetError

        ref_tweet = next(filter(lambda t: t.type == "replied_to", tweet.referenced_tweets))
        ref_tweet = cast(ReferencedTweet, ref_tweet)
        if ref_tweet is None:
            logger.error(f"in_reply_to_user_id is set for tweet {tweet.id}, but no referenced_tweets exist")
            raise NoReferencedTweetError

        return ref_tweet.id

    async def fetch_and_process_tweet(self, tweet_id: int) -> Tweet:
        """Gets and returns the tweet in question and updates the conversation and alt texts
        Raises a TwitterException if anything goes wrong
        """
        # Fetch tweet:
        api = TwitterApi(**twitter_keys)
        expansions = ["author_id", "in_reply_to_user_id", "referenced_tweets.id"]
        response = await api.get_tweet(id=tweet_id, expansions=expansions)

        # Error handling:
        if not isinstance(response, Response):
            logger.error(f"API did not return a Response while fetching tweet {tweet_id}")
            raise TwitterError

        includes: dict[str, Any]
        tweet: Tweet
        (tweet, includes, errors, _) = response
        if errors:
            for error in errors:
                logger.error(f"Error while fetching tweet {tweet_id}: {error}")
            raise TwitterError

        users = includes.get("users")
        if not users:
            # This condition filters both for None and an empty list
            logger.error(f"API did not return users while fetching tweet {tweet_id}")
            raise TwitterError
        users = cast(list[User], users)

        author = users[0]

        # Process the data that is not contained in the Tweet class:
        self.alt_texts.append(f'Tweet by @{author.username}: {tweet.text}')
        self.conversation.add(author.id)
        self.thread = range(self.thread.start, self.thread.stop + 1)

        return tweet

    async def fetch_thread(self):
        try:
            replyee_id = self.get_replyee_id(self.tweet)
            if replyee_id is None:
                self.add_header()
                self.add_tweet()
                return

            while replyee_id is not None:
                potential_reblog = db.get_tweet(replyee_id)
                if potential_reblog is None:
                    replyee_tweet = await self.fetch_and_process_tweet(replyee_id)
                    replyee_id = self.get_replyee_id(replyee_tweet)
                else:
                    (tweet_index, reblog_id, blogname) = potential_reblog
                    self.thread = range(self.thread.start + tweet_index, self.thread.stop + tweet_index)
                    self.reblog = (reblog_id, blogname)
                    break

            self.add_header()
            self.alt_texts.reverse()
            self.add_tweets()
        except TwitterError as e:
            logger.error(f"Something went wrong fetching the thread: {e}")

    async def post(self, blogname: str, api: TumblrApi) -> dict[str, Any]:
        await self.fetch_thread()

        response = await super().post(blogname, api)

        errors = response.get("errors")
        post_id = response.get("id")
        if errors:
            logger.error(f"Tumblr response contained errors: {errors}")
        elif post_id:
            db.add_tweet(self.tweet.id, self.thread.stop, post_id, blogname)
        else:
            logger.error("Tumblr response contained no errors, but also no post id")

        return response
