import os
from pprint import pprint
from time import sleep
from typing import List, Type, Union, TypeAlias
from pytumblr2 import TumblrRestClient as TumblrClient
from tweepy import Client as TwitterClient
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from tweepy import Response, StreamingClient, StreamResponse, StreamRule, Tweet
from config import twitter_names
import random

ContentBlock: TypeAlias = dict[str, Union[str, dict[str, str], List[dict[str, str]]]]


class TweetListener(StreamingClient):

    driver: Chrome
    tumblr_client: TumblrClient
    twitter_client: TwitterClient
    blogname: str

    def __init__(
        self,
        tumblr_client: TumblrClient,
        twitter_client: TwitterClient,
        blogname: str,
        bearer_token: str,
        return_type: Type[Response] = Response,
        wait_on_rate_limit: bool = False,
        **kwargs: str,
    ):
        super().__init__(
            bearer_token,
            return_type=return_type,
            wait_on_rate_limit=wait_on_rate_limit,
            **kwargs,
        )

        self.tumblr_client = tumblr_client
        self.twitter_client = twitter_client
        self.blogname = blogname

        # Setup the browser to take pictures
        options = Options()
        options.headless = True
        self.driver = Chrome(options=options)

        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(2000, 2000)

    def on_response(self, response: StreamResponse) -> None:
        tweet: Tweet
        rules: List[StreamRule]
        (tweet, includes, errors, rules) = response

        if errors:
            for error in errors:
                pprint(error)
        else:
            author = includes["users"][0]
            username = author["username"]

            identifier = "tweet{}".format(tweet.id)
            url = "https://twitter.com/{}/status/{}".format(username, tweet.id)

            alt_texts = ["Tweet by @{}: {}".format(username, tweet.text)]
            replied_to: List[int] = []
            thread_depth = 1

            current_tweet: Tweet = tweet
            while current_tweet.in_reply_to_user_id is not None:

                replied_to.append(current_tweet.in_reply_to_user_id)

                for referenced in current_tweet.referenced_tweets:
                    if referenced.type == "replied_to":
                        thread_depth += 1

                        expansions = [
                            "author_id",
                            "in_reply_to_user_id",
                            "attachments.media_keys",
                            "referenced_tweets.id",
                        ]
                        ref_response = self.twitter_client.get_tweet(
                            id=referenced.id, expansions=expansions
                        )

                        if isinstance(ref_response, Response):
                            ref_tweet: Tweet
                            (ref_tweet, ref_includes, ref_errors, _) = ref_response
                            if ref_errors:
                                pprint(ref_errors)
                            else:
                                ref_author = ref_includes["users"][0]
                                alt_texts.append(
                                    "Tweet by @{}: {}".format(
                                        ref_author["username"], ref_tweet.text
                                    )
                                )
                                current_tweet = ref_tweet
                        else:
                            print("Getting replied to tweet failed somehow")

            filenames = self.render_thread(url, identifier, thread_depth, thread_depth)
            media_sources = {
                "tweet{}".format(i): filename for (i, filename) in enumerate(filenames)
            }

            content = [
                self.header_block(author.id, replied_to),
            ]

            for (i, alt_text) in enumerate(reversed(alt_texts)):
                if i == thread_depth:
                    block = self.tweet_block("tweet{}".format(i), alt_text, url)
                else:
                    block = self.tweet_block("tweet{}".format(i), alt_text)

                content.append(block)

            self.tumblr_client.create_post(
                blogname=self.blogname,
                content=content,
                tags=["automated"],
                media_sources=media_sources,
            )

            for filename in filenames:
                os.remove(filename)

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
                replies += " and {}!".format(next(people_iter))

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

    def on_connect(self) -> None:
        print("Listening to twitter... (connected)")

    def render_tweet(
        self, url: str, filename_prefix: str, conversation_lenth: int = 1
    ) -> None:
        self.render_thread(url, filename_prefix, conversation_lenth)

    def render_thread(
        self, url: str, filename_prefix: str, tweet_index: int, thread_height: int = 1
    ) -> List[str]:
        """Renders a tweet, and the tweets it was responding to

        :param url: The url of the tweet to be rendered
        :param filename_prefix: The n'th tweet will be saved to "filename_prefix-n.png"
        :param tweet_index: The index of the tweet, starting from 1.
            (If there were two tweets before this one, the tweet index would be 3)
        :thread_height: How many tweets to render, must be strictly postive and smaller or equal to the tweet index
            Default is 1
        :returns: A list of filenames, where the rendered tweets are stored
        """
        # Variables keeping track of current actual view of the tweets, not the viewport
        footer_height = 225
        view_bottom = self.driver.get_window_size()["height"] - footer_height
        header_bottom = 53

        self.driver.get(url)

        # Just to make sure all elements load first
        sleep(1.5)

        # Scroll to top
        body_element = self.driver.find_element(By.XPATH, "/html/body")
        # I'm not quite sure why, but we need to do this twice, else it doesn't fully scroll to the top
        body_element.send_keys(Keys.CONTROL + Keys.HOME)
        body_element.send_keys(Keys.CONTROL + Keys.HOME)

        # Again make sure all elements (images etc) are loaded
        sleep(1.5)

        tweet_xpath = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div/div[{}]"

        filenames = []

        for i in range(tweet_index - thread_height, tweet_index + 1):
            tweet_element = self.driver.find_element(By.XPATH, tweet_xpath.format(i))

            tweet_top = tweet_element.rect["y"]
            tweet_bottom = tweet_top + tweet_element.rect["height"]

            if tweet_bottom >= view_bottom:
                to_scroll = tweet_top - header_bottom
                ActionChains(self.driver).scroll_by_amount(0, to_scroll).perform()
                view_bottom += to_scroll
                header_bottom += to_scroll

                # Because we scrolled we now need to relocate the tweet
                tweet_element = self.driver.find_element(
                    By.XPATH, tweet_xpath.format(i)
                )
            filename = "{}-{}.png".format(filename_prefix, i)
            tweet_element.screenshot(filename)
            filenames.append(filename)

        return filenames

    def __del__(self) -> None:
        self.driver.close()
