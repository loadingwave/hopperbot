from time import sleep
from typing import List
import logging

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class Renderer(Chrome):

    # Twitter variables
    FOOTER_HEIGHT = 225
    HEADER_HEIGHT = 53
    TWEET_XPATH = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div/div[{}]"

    def __init__(self) -> None:

        logger = logging.getLogger("selenium.webdriver.remote.remote_connection")
        logger.setLevel(logging.WARNING)

        options = Options()
        options.headless = True
        super().__init__(options=options)
        self.set_window_position(0, 0)
        self.set_window_size(2000, 2000)

    def render_tweets(self, url: str, filename_prefix: str, tweet_index: int, thread_height: int = 1) -> List[str]:
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
        view_bottom = self.get_window_size()["height"] - self.FOOTER_HEIGHT
        view_top = self.HEADER_HEIGHT

        self.get(url)

        # Get the body element, so that we can send keypresses to it
        body_element = self.find_element(By.XPATH, "/html/body")

        # I'm not quite sure why, but we need to do this twice, else it doesn't fully scroll to the top
        body_element.send_keys(Keys.CONTROL + Keys.HOME)
        sleep(1)
        body_element.send_keys(Keys.CONTROL + Keys.HOME)

        # Again make sure all elements (images etc) are loaded
        sleep(1)

        filenames = []

        # tweet_index - thread_height is the index of the first tweet to be rendered
        # incrementing by 1 is needed because the 0th element of the div is the header, not the first tweet
        for i in range(tweet_index - thread_height + 1, tweet_index + 1):
            tweet_element = self.find_element(By.XPATH, self.TWEET_XPATH.format(i))

            tweet_top = tweet_element.rect["y"]
            tweet_bottom = tweet_top + tweet_element.rect["height"]

            if tweet_bottom >= view_bottom:
                to_scroll = tweet_top - view_top
                ActionChains(self).scroll_by_amount(0, to_scroll).perform()
                view_bottom += to_scroll
                view_top += to_scroll

                # Because we scrolled we now need to relocate the tweet
                tweet_element = self.find_element(By.XPATH, self.TWEET_XPATH.format(i))

            filename = f"{filename_prefix}-{i}.png"
            tweet_element.screenshot(filename)
            filenames.append(filename)

        return filenames
