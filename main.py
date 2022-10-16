from pytumblr2 import TumblrRestClient as TumblrClient
from tweepy import Client as TwitterClient
from tweepy import StreamRule

from hopperbot.config import tumblr_keys, twitter_keys
from hopperbot.core import TweetListener


def main() -> None:

    tumblr_client = TumblrClient(**tumblr_keys)
    twitter_client = TwitterClient(**twitter_keys)

    # Mypy gives a typing error here, this is a known issue: https://github.com/python/mypy/issues/1969
    twitter_sc = TweetListener(tumblr_client=tumblr_client, twitter_client=twitter_client, blogname="test37", **twitter_keys)  # type: ignore

    rule = StreamRule(
        "from:space_stew OR from:tapwaterthomas OR from:Etherealbro_", "Thomas"
    )
    twitter_sc.add_rules(rule)

    expansions = [
        "author_id",
        "in_reply_to_user_id",
        "attachments.media_keys",
        "referenced_tweets.id",
    ]

    media_fields = ["alt_text", "type", "url"]

    twitter_sc.filter(expansions=expansions, media_fields=media_fields)


if __name__ == "__main__":
    main()
