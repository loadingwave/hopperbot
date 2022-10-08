# import pytumblr2
import tweepy

from typing import Type

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

from config import twitter_keys  # , tumblr_keys
import logging
import time

# by default StreamingClient writes debug information wiht logging level DEBUG,
# this makes sure its written to file
logging.basicConfig(filename="tweets.log", encoding="utf-8", level=logging.DEBUG)


def renderTweet(driver: webdriver.Firefox, tweet_id: int) -> None:
    TWEET_LOOKUP_URL = "https://twitter.com/twitter/statuses/{}"

    url = TWEET_LOOKUP_URL.format(tweet_id)
    driver.get(url)

    # Just to make sure all elements load first
    time.sleep(2)

    # Screenshot the Tweet
    XPATH = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div/div[1]/div/div/div[1]/article"
    web_element = driver.find_element(By.XPATH, XPATH)
    img = web_element.screenshot_as_png

    # Write the image data to a file
    filename = "tweet-{}.png".format(tweet_id)
    with open(filename, "wb") as file:
        file.write(img)


class TweetListener(tweepy.StreamingClient):

    driver: webdriver.Firefox

    def __init__(
        self,
        bearer_token: str,
        return_type: Type[tweepy.Response] = tweepy.Response,
        wait_on_rate_limit: bool = False,
        **kwargs: str,
    ):
        super().__init__(
            bearer_token,
            return_type=return_type,
            wait_on_rate_limit=wait_on_rate_limit,
            **kwargs,
        )

        # Setup the browser to take pictures
        options = Options()
        options.headless = True
        self.driver = webdriver.Firefox(options=options)

        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(2000, 2000)

    def on_tweet(self, tweet: tweepy.Tweet) -> None:
        renderTweet(self.driver, tweet.id)

    def __del__(self) -> None:
        self.driver.close()


twitter_sc = TweetListener(**twitter_keys)

rule = tweepy.StreamRule("from:space_stew OR from:tapwaterthomas", "thomas")
twitter_sc.add_rules(rule)

twitter_sc.filter()
