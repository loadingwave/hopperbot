from time import sleep
import os
from typing import Type, List, Union
from pprint import pprint

from pytumblr2 import TumblrRestClient
from tweepy import StreamingClient, Response, StreamResponse, StreamRule, Tweet

# from tweepy import Client as TwitterClient
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains


class TweetListener(StreamingClient):

    driver: Chrome
    tumblr_client: TumblrRestClient
    # twitter_client: TwitterClient
    blogname: str

    def __init__(
        self,
        tumblr_client: TumblrRestClient,
        # twitter_client: TwitterClient,
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
        # self.twitter_client = twitter_client
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

        pprint(response)

        if errors:
            for error in errors:
                pprint(error)
        else:
            # Can we just assume the first user is the author?
            username = includes["users"][0]["username"]

            identifier = "tweet-{}".format(tweet.id)
            url = "https://twitter.com/{}/status/{}".format(username, tweet.id)
            filename = "tweet-{}.png".format(tweet.id)
            alt_text = "A tweet by @{}: {}".format(username, tweet.text)

            self.render_tweet(url, filename)

            self.tumblr_client.create_post(
                blogname=self.blogname,
                content=[
                    self.header_block(rules),
                    self.tweet_block(identifier, alt_text, url),
                ],
                tags=["automated"],
                media_sources={identifier: filename},
            )

            os.remove(filename)

    def header_block(self, rules: List[StreamRule]) -> dict[str, str]:
        name = rules[0].tag.capitalize()
        return {
            "type": "text",
            "text": "{} posted on Twitter".format(name),
        }

    def tweet_block(
        self, identifier: str, alt_text: str, url: str
    ) -> dict[str, Union[str, dict[str, str], List[dict[str, str]]]]:
        return {
            "type": "image",
            "media": [
                {
                    "type": "image/png",
                    "identifier": identifier,
                }
            ],
            "alt_text": alt_text,
            "attribution": {
                "type": "app",
                "url": url,
                "app_name": "Twitter",
                "display_text": "View on Twitter",
            },
        }

    def on_connect(self) -> None:
        print("Listening to twitter... (connected)")

    def render_tweet(
        self, url: str, filename: str, conversation_lenth: int = 1
    ) -> None:
        self.driver.get(url)

        # Just to make sure all elements load first
        sleep(2)

        # Screenshot the Tweet
        XPATH = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div/div[1]/div/div/div[1]/article"
        web_element = self.driver.find_element(By.XPATH, XPATH)
        img = web_element.screenshot_as_png

        # Write the image data to a file
        with open(filename, "wb") as file:
            file.write(img)

    def render_thread(self, url: str, tweet_id: str, thread_depth: int = 1) -> None:

        # Variables keeping track of current actual view of the tweets, not the viewport
        footer_height = 225
        view_bottom = self.driver.get_window_size()["height"] - footer_height
        header_bottom = 53

        self.driver.get(url)

        # Just to make sure all elements load first
        sleep(1.5)

        # Scroll to top
        scrolling_xpath = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div"
        full_element = self.driver.find_element(By.XPATH, scrolling_xpath)
        self.driver.execute_script("arguments[0].scrollIntoView();", full_element)

        # Again make sure all elements (images etc) are loaded
        sleep(1.5)

        tweet_xpath = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div/div[{}]"

        for i in range(1, thread_depth + 1):
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

            tweet_element.screenshot("tweet{}-{}.png".format(tweet_id, i))

    def __del__(self) -> None:
        self.driver.close()
