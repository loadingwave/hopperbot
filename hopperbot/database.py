import logging
import sqlite3 as sqlite
from typing import Tuple, Union
from hopperbot.people import Person, adapt_person, convert_person

logger = logging.getLogger("Database")
logger.setLevel(logging.INFO)

sqlite.register_adapter(Person, adapt_person)
sqlite.register_converter("PERSON", convert_person)


def init_database() -> None:
    con = sqlite.connect("tweets.db", detect_types=sqlite.PARSE_DECLTYPES)
    cur = con.cursor()

    response = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tweets'").fetchone()

    if response is None:
        logger.info("Created tweets table")
        cur.execute(
            "CREATE TABLE tweets(tweet_id INTEGER PRIMARY KEY, tweet_index INTEGER, reblog_id INTEGER, blogname STRING)"
        )

    response = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='twitter_names'").fetchone()

    if response is None:
        logger.info("Created tweets table")
        cur.execute(
            "CREATE TABLE tweets(tweet_id INTEGER PRIMARY KEY, tweet_index INTEGER, reblog_id INTEGER, blogname STRING)"
        )

    con.commit()
    con.close()


def get_tweet(tweet_id: int) -> Union[None, Tuple[int, int, str]]:
    tweets_db = sqlite.connect("tweets.db", detect_types=sqlite.PARSE_DECLTYPES)

    result = None

    with tweets_db:
        cur = tweets_db.execute("SELECT tweet_index, reblog_id, blogname FROM tweets WHERE tweet_id = ?", [tweet_id])
        result = cur.fetchone()

    tweets_db.close()

    return result


def add_tweet(tweet_id: int, tweet_index: int, tumblr_id: int, blogname: str) -> None:
    tweets_db = sqlite.connect("tweets.db", detect_types=sqlite.PARSE_DECLTYPES)

    with tweets_db:
        tweets_db.execute(
            "INSERT INTO tweets(tweet_id, tweet_index, reblog_id, blogname) VALUES(?, ?, ?, ?)",
            (tweet_id, tweet_index, tumblr_id, blogname),
        )
        logger.debug(f"Inserted tweet id {tweet_id} with tumblr id: {tumblr_id}")

    tweets_db.close()
