import os
import random
from pprint import pprint
from time import sleep
from typing import List, TypeAlias, Union

from pytumblr2 import TumblrRestClient as TumblrClient
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from tweepy import Client as TwitterClient
from tweepy import Response, StreamRule, Tweet

from hopperbot.config import tumblr_keys, twitter_keys, twitter_names


ContentBlock: TypeAlias = dict[str, Union[str, dict[str, str], List[dict[str, str]]]]


tumblr_client = TumblrClient(**tumblr_keys)
blogname = "test37"
print("Tumblr setup complete!")

twitter_client = TwitterClient(**twitter_keys)
print("Twitter setup complete!")

options = Options()
options.headless = True
driver = Chrome(options=options)

driver.set_window_position(0, 0)
driver.set_window_size(2000, 2000)

print("Driver setup complete!")


def on_response(response: Response) -> None:
    tweet: Tweet
    _: List[StreamRule]
    (tweet, includes, errors, _) = response

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
        thread_index = 1

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
                    ref_response = twitter_client.get_tweet(
                        id=referenced.id, expansions=expansions
                    )
                    if isinstance(ref_response, Response):
                        ref_tweet: Tweet
                        (ref_tweet, ref_includes, ref_errors, _) = ref_response
                        if ref_errors:
                            pprint(ref_errors)
                        else:
                            ref_author = ref_includes["users"][0]
                            alt = "Tweet by @{}: {}".format(
                                ref_author["username"], ref_tweet.text
                            )
                            alt_texts.append(alt)
                            print("Replied to:", alt)

                            current_tweet = ref_tweet
                    else:
                        print("Getting replied to tweet failed somehow")

        thread_index = thread_depth
        print("Thread is {} tweets long".format(thread_index))

        filenames = render_thread(url, identifier, thread_index, thread_depth)

        print("Tweets rendered:", filenames)

        media_sources = {
            "tweet{}".format(i): filename for (i, filename) in enumerate(filenames)
        }

        content = [
            header_block(author.id, replied_to),
        ]

        for (i, alt_text) in enumerate(reversed(alt_texts)):
            if i == thread_depth:
                block = tweet_block("tweet{}".format(i), alt_text, url)
            else:
                block = tweet_block("tweet{}".format(i), alt_text)

            content.append(block)

        pprint(media_sources)
        pprint(content)

        r = tumblr_client.create_post(
            blogname=blogname,
            content=content,
            tags=["automated"],
            media_sources=media_sources,
        )

        pprint(r)

        for filename in filenames:
            os.remove(filename)

        print("Removed files!")


def header_block(user_id: int, replied_to: List[int] = []) -> ContentBlock:
    (name, pronouns) = twitter_names[user_id]
    if replied_to:

        people = {
            twitter_names.get(i, "someone")[0] for i in replied_to if i in twitter_names
        }

        if name in people:
            people.remove(name)
            people.add(random.choice(pronouns))

        print("People in conversation:", people)

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
    identifier: str, alt_text: str, url: Union[str, None] = None
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


def render_thread(
    url: str, filename_prefix: str, tweet_index: int, thread_height: int = 1
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
    view_bottom = driver.get_window_size()["height"] - footer_height
    header_bottom = 53

    driver.get(url)

    print("Got webpage!")

    # Just to make sure all elements load first
    print("Sleeping...")
    sleep(1.5)

    driver.save_screenshot("twitter_fullscreen1.png")

    # Scroll to top
    body_element = driver.find_element(By.XPATH, "/html/body")
    # I'm not quite sure why, but we need to do this twice, else it doesn't fully scroll to the top
    body_element.send_keys(Keys.CONTROL + Keys.HOME)
    body_element.send_keys(Keys.CONTROL + Keys.HOME)

    # Again make sure all elements (images etc) are loaded
    print("Scrolled to top, sleeping...")
    sleep(1.5)

    driver.save_screenshot("twitter_fullscreen2.png")

    tweet_xpath = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div/div[{}]"

    filenames = []

    for i in range(tweet_index - thread_height + 1, tweet_index + 1):
        tweet_element = driver.find_element(By.XPATH, tweet_xpath.format(i))

        tweet_top = tweet_element.rect["y"]
        tweet_bottom = tweet_top + tweet_element.rect["height"]

        if tweet_bottom >= view_bottom:
            to_scroll = tweet_top - header_bottom
            ActionChains(driver).scroll_by_amount(0, to_scroll).perform()
            view_bottom += to_scroll
            header_bottom += to_scroll

            print("Scrolled by", to_scroll)

            # Because we scrolled we now need to relocate the tweet
            tweet_element = driver.find_element(By.XPATH, tweet_xpath.format(i))

        filename = "{}-{}.png".format(filename_prefix, i)
        tweet_element.screenshot(filename)
        filenames.append(filename)

    return filenames


expansions = [
    "author_id",
    "in_reply_to_user_id",
    "attachments.media_keys",
    "referenced_tweets.id",
]

id = 1581259976437530625

response = twitter_client.get_tweet(id=id, expansions=expansions)
print("Got response!")
if isinstance(response, Response):
    on_response(response)

# user_id = 1478064563358740481
# replies = [1478064563358740481, 1478064563358740481]

# block = header_block(user_id, replies)

# pprint(block)
