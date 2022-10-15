from pprint import pprint
import pytumblr2
import tweepy

from typing import Type

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

from config import twitter_keys, tumblr_keys
import time

blog = "test37"


def renderTweet(driver: webdriver.Firefox, url: str, filename: str) -> None:

    driver.get(url)

    # Just to make sure all elements load first
    time.sleep(2)

    # Screenshot the Tweet
    XPATH = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div/div[1]/div/div/div[1]/article"
    web_element = driver.find_element(By.XPATH, XPATH)
    img = web_element.screenshot_as_png

    # Write the image data to a file
    with open(filename, "wb") as file:
        file.write(img)


class TweetListener(tweepy.StreamingClient):

    driver: webdriver.Firefox
    tumblr_client: pytumblr2.TumblrRestClient

    def __init__(
        self,
        tumblr_client: pytumblr2.TumblrRestClient,
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

        self.tumblr_client = tumblr_client

        # Setup the browser to take pictures
        options = Options()
        options.headless = True
        self.driver = webdriver.Firefox(options=options)

        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(2000, 2000)

    def on_response(self, response: tweepy.StreamResponse) -> None:
        (tweet, includes, errors, matching_rules) = response

        print("Someone tweeted!")
        for error in errors:
            pprint(error)

        username = includes["users"][0]["username"]
        rule_tags = [rule.tag for rule in matching_rules]

        header_content_block = {
            "type": "text",
            "text": "{} posted on Twitter!".format(rule_tags[0]),
        }

        identifier = "tweet-{}".format(tweet.id)
        url = "https://twitter.com/{}/status/{}".format(username, tweet.id)
        filename = "tweet-{}.png".format(tweet.id)
        alt_text = "A tweet by @{}: {}".format(username, tweet.text)

        renderTweet(self.driver, url, filename)

        tweet_content_block = {
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

        self.tumblr_client.create_post(
            blog,
            content=[header_content_block, tweet_content_block],
            tags=["automated"],
            media_sources={identifier: filename},
        )

    def on_connect(self) -> None:
        print("Listening to twitter... (connected)")

    def __del__(self) -> None:
        self.driver.close()


def main() -> None:

    tumblr_client = pytumblr2.TumblrRestClient(**tumblr_keys)

    twitter_sc = TweetListener(tumblr_client=tumblr_client, **twitter_keys)

    rule = tweepy.StreamRule("from:space_stew OR from:tapwaterthomas", "Thomas")
    twitter_sc.add_rules(rule)

    twitter_sc.filter(expansions="author_id", user_fields=["username"])


if __name__ == "__main__":
    main()
