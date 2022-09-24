import pytumblr2
import tweepy
from config import tumblr_keys, twitter_keys


class TweetListener(tweepy.StreamingClient):
    def on_tweet(self, tweet: tweepy.Response) -> None:
        print(tweet)


BLOG = "test37"

tumblr_client = pytumblr2.TumblrRestClient(**tumblr_keys)

# Streaming Client
twitter_sc = tweepy.StreamingClient(**twitter_keys)

rule = tweepy.StreamRule("from:space_stew OR from:tapwaterthomas", "thomas")

twitter_sc.add_rules(rule)

print("Twitter starts filtering...")
twitter_sc.sample()
