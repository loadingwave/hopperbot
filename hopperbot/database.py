import logging
import sqlite3 as sqlite
from typing import Tuple, Union

logger = logging.getLogger(__name__)


def get_tweet(tweet_id: int) -> Union[None, Tuple[int, int, str]]:
    tweets_db = sqlite.connect("tweets.db", detect_types=sqlite.PARSE_DECLTYPES)

    result = None

    with tweets_db:
        cur = tweets_db.execute("SELECT tweet_index, reblog_id, blogname FROM tweets WHERE tweet_id = ?", [tweet_id])
        response = cur.fetchone()
        if response is None:
            result = None
        else:
            (tweet_index, reblog_id, blogname) = response
            result = (tweet_index, reblog_id, blogname)

    tweets_db.close()

    return result


def add_tweet(tweet_id: int, tweet_index: int, tumblr_id: int, blogname: str) -> None:
    tweets_db = sqlite.connect("tweets.db", detect_types=sqlite.PARSE_DECLTYPES)

    with tweets_db:
        tweets_db.execute(
            "INSERT INTO tweets(tweet_id, tweet_index, reblog_id, blogname) VALUES(?, ?, ?, ?)",
            (tweet_id, tweet_index, tumblr_id, blogname),
        )

    tweets_db.close()
