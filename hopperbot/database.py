import logging
import sqlite3 as sqlite
from typing import Tuple, Optional
from hopperbot.people import Person, adapt_person, convert_person

logger = logging.getLogger("Database")
logger.setLevel(logging.INFO)

sqlite.register_adapter(Person, adapt_person)
sqlite.register_converter("PERSON", convert_person)

FILENAME = "tweets.db"


def init_database() -> None:
    con = sqlite.connect(FILENAME, detect_types=sqlite.PARSE_DECLTYPES)
    cur = con.cursor()

    tweets = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tweets'").fetchone()

    if tweets is None:
        logger.info("Created tweets table")
        cur.execute(
            "CREATE TABLE tweets(tweet_id INTEGER PRIMARY KEY, tweet_index INTEGER, reblog_id INTEGER, blogname STRING)"
        )

    twitter_names = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='twitter_names'").fetchone()

    if twitter_names is None:
        logger.info("Created twitter names table")
        cur.execute(
            "CREATE TABLE twitter_names(twitter_id INTEGER PRIMARY KEY, person PERSON)"
        )

    con.commit()
    con.close()


def get_tweet(tweet_id: int) -> Optional[Tuple[int, int, str]]:
    tweets_db = sqlite.connect(FILENAME, detect_types=sqlite.PARSE_DECLTYPES)

    result = None

    with tweets_db:
        cur = tweets_db.execute("SELECT tweet_index, reblog_id, blogname FROM tweets WHERE tweet_id = ?", [tweet_id])
        result = cur.fetchone()

    tweets_db.close()

    return result


def add_tweet(tweet_id: int, tweet_index: int, tumblr_id: int, blogname: str) -> None:
    tweets_db = sqlite.connect(FILENAME, detect_types=sqlite.PARSE_DECLTYPES)

    with tweets_db:
        tweets_db.execute(
            "INSERT INTO tweets(tweet_id, tweet_index, reblog_id, blogname) VALUES(?, ?, ?, ?)",
            (tweet_id, tweet_index, tumblr_id, blogname),
        )
        logger.debug(f"Inserted tweet id {tweet_id} with tumblr id: {tumblr_id}")

    tweets_db.close()


def add_person(twitter_id: int, person: Person) -> None:
    database = sqlite.connect(FILENAME, detect_types=sqlite.PARSE_DECLTYPES)

    with database:
        database.execute(
            "INSERT INTO twitter_names(twitter_id, person) VALUES(?, ?)",
            (twitter_id, person),
        )
        logger.debug(f"Inserted person {person.name} with twitter id: {twitter_id} into twitter names table")

    database.close()


def get_person(twitter_id: int) -> Optional[Person]:
    database = sqlite.connect(FILENAME, detect_types=sqlite.PARSE_DECLTYPES)

    result = None

    with database:
        cur = database.execute("SELECT person FROM twitter_names WHERE tweet_id = ?", [twitter_id])
        result = cur.fetchone()

    database.close()

    return result
