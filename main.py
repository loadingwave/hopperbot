from hopperbot.config import tumblr_keys, twitter_keys
from hopperbot.core import TweetListener
from pytumblr2 import TumblrRestClient
from tweepy import StreamRule


def main() -> None:

    tumblr_client = TumblrRestClient(**tumblr_keys)

    # Mypy gives a typing error here, this is a known issue: https://github.com/python/mypy/issues/1969
    twitter_sc = TweetListener(tumblr_client=tumblr_client, blogname="test37", **twitter_keys)  # type: ignore

    rule = StreamRule("from:space_stew OR from:tapwaterthomas", "Thomas")
    twitter_sc.add_rules(rule)

    expansions = [
        "author_id",
        "referenced_tweets.id",
        "in_reply_to_user_id",
        "attachments.media_keys",
        "entities.mentions.username",
        "referenced_tweets.id.author_id",
    ]

    tweet_fields = ["conversation_id"]

    media_fields = ["alt_text", "type", "url"]

    twitter_sc.filter(
        expansions=expansions, tweet_fields=tweet_fields, media_fields=media_fields
    )


if __name__ == "__main__":
    main()
