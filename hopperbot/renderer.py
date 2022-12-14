import logging
from time import sleep
from typing import Optional

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.remote_connection import LOGGER as selenium_logger

selenium_logger.setLevel(logging.INFO)
logger = logging.getLogger("Renderer")
logger.setLevel(logging.DEBUG)


class Renderer(Chrome):

    # Twitter variables
    FOOTER_HEIGHT = 225
    HEADER_HEIGHT = 53
    TWEET_XPATH = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div/div[{}]/div/div/div[1]/article"

    def __init__(self) -> None:
        options = Options()
        options.headless = True
        super().__init__(options=options)
        self.set_window_position(0, 0)
        self.set_window_size(2000, 2000)

    def render_tweets(self, url: str, filename_prefix: str, thread_range: Optional[range]) -> list[str]:
        """Renders a tweet, and the tweets it was responding to

        Parameters
        ----------
        url : str
            The url of the tweet to be rendered
        filename_prefix : str
            The n'th tweet will be saved to "filename_prefix-n.png"
        tweet_index : int
            The range of tweets to be rendered, with the first tweet in the thread having index 0.

        Returns
        -------
        List[str]
            A list of filenames, where the rendered tweets are stored
        """
        if thread_range is None:
            self.get(url)
            sleep(2)
            tweet_element = self.find_element(By.XPATH, self.TWEET_XPATH.format(1))
            filename = filename_prefix + "1.png"
            tweet_element.screenshot(filename)
            return [filename]

        elif thread_range.start < 0:
            raise ValueError("Thread range should have positive start")
        elif thread_range.step < 0:
            raise ValueError("Thread range should have positive step")

        # Variables keeping track of current actual view of the tweets, not the viewport
        view_bottom = self.get_window_size()["height"] - self.FOOTER_HEIGHT
        view_top = self.HEADER_HEIGHT

        self.get(url)

        # Get the body element, so that we can send keypresses to it
        body_element = self.find_element(By.XPATH, "/html/body")

        body_element.send_keys(Keys.CONTROL + Keys.HOME)

        for i in range((thread_range.stop // 10) + 1):
            # React doesn't load all the tweets in at first, so when we scroll
            # to "home", new tweets might appear above it, the number 10 seems
            # to be this border where it needs to fetch more tweets, (why the
            # extra '+ 1' is nesesary I also don't know, but it is)
            sleep(1)
            body_element.send_keys(Keys.CONTROL + Keys.HOME)

        # Again we sleep make sure all elements (images etc) are loaded
        sleep(1)

        filenames = []

        for i in thread_range:

            # The first elment in the div is the header, so we need to incrment i by one
            tweet_element = self.find_element(By.XPATH, self.TWEET_XPATH.format(i + 1))

            tweet_top = tweet_element.rect["y"]
            tweet_bottom = tweet_top + tweet_element.rect["height"]

            if tweet_bottom >= view_bottom:
                to_scroll = tweet_top - view_top
                ActionChains(self).scroll_by_amount(0, to_scroll).perform()
                view_bottom += to_scroll
                view_top += to_scroll

                logger.debug(f"Scrolled by {to_scroll} while rendering {url}")

                # Because we scrolled we now need to relocate the tweet
                tweet_element = self.find_element(By.XPATH, self.TWEET_XPATH.format(i + 1))

            filename = f"{filename_prefix}-{i}.png"
            tweet_element.screenshot(filename)
            filenames.append(filename)

            logger.debug(f"Created screenshot {filename}")

        return filenames


RENDERER = Renderer()
