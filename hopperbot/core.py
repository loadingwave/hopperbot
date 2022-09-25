# import pytumblr2
# import tweepy

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

# from config import tumblr_keys, twitter_keys
import logging
import time

# by default StreamingClient writes debug information wiht logging level DEBUG,
# this makes sure its written to file
logging.basicConfig(filename="example.log", encoding="utf-8", level=logging.DEBUG)

# Setup the browser to take pictures
options = Options()
options.headless = True
driver = webdriver.Firefox(options=options)

driver.set_window_position(0, 0)
driver.set_window_size(2000, 2000)

TWEET_LOOKUP_URL = "https://twitter.com/twitter/statuses/{}"

url = TWEET_LOOKUP_URL.format(1573968863372378112)
driver.get(url)

# Just to make sure all elements load first
time.sleep(2)

# Screenshot the Tweet
# XPATH = "/html/body/div/div/div/div[2]/main/div/div/div/div[1]/div/div[2]/div/section/div/div/div[1]/div/div/article"
XPATH = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div/div[1]/div/div/div[1]/article"
web_element = driver.find_element(By.XPATH, XPATH)
img = web_element.screenshot_as_png

# Write the image data to a file
with open("tweet.png", "wb") as file:
    file.write(img)

# Close the headless browser
driver.close()

# class TweetListener(tweepy.StreamingClient):
#     def on_tweet(self, tweet: tweepy.Tweet) -> None:
#         url = TWEET_LOOKUP_URL.format(tweet.id)
#         driver.get(url)
#         print(tweet)


# BLOG = "test37"

# tumblr_client = pytumblr2.TumblrRestClient(**tumblr_keys)

# # Streaming Client
# twitter_sc = TweetListener(**twitter_keys)

# rule = tweepy.StreamRule("from:space_stew OR from:tapwaterthomas", "thomas")

# twitter_sc.add_rules(rule)

# print("Twitter starts filtering...")
# twitter_sc.filter()
