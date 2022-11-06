import logging
import sqlite3 as sqlite
from typing import Tuple, Optional
from hopperbot.people import Person, adapt_person, convert_person

logger = logging.getLogger("Database")
logger.setLevel(logging.DEBUG)

sqlite.register_adapter(Person, adapt_person)
sqlite.register_converter("PERSON", convert_person)

FILENAME = "hopperbot.db"


def init_database() -> None:
    con = sqlite.connect(FILENAME, detect_types=sqlite.PARSE_DECLTYPES)
    cur = con.cursor()

    tweets = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tweets'").fetchone()

    if tweets is None:
        logger.info("Created table: tweets")
        cur.execute(
            "CREATE TABLE tweets(tweet_id INTEGER PRIMARY KEY, tweet_index INTEGER, reblog_id INTEGER, blogname STRING)"
        )

    twitter_names = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='twitter_names'").fetchone()

    if twitter_names is None:
        logger.info("Created table: twitter_names")
        cur.execute(
            "CREATE TABLE twitter_names(twitter_id INTEGER PRIMARY KEY, person PERSON)"
        )

    con.commit()
    con.close()


def add_tweet(tweet_id: int, tweet_index: int, tumblr_id: int, blogname: str) -> None:
    database = sqlite.connect(FILENAME, detect_types=sqlite.PARSE_DECLTYPES)

    with database:
        database.execute(
            "INSERT INTO tweets(tweet_id, tweet_index, reblog_id, blogname) VALUES(?, ?, ?, ?)",
            (tweet_id, tweet_index, tumblr_id, blogname),
        )
        logger.debug(f"Inserted tweet id {tweet_id} with tumblr id: {tumblr_id}")

    database.close()


def get_tweet(tweet_id: int) -> Optional[Tuple[int, int, str]]:
    database = sqlite.connect(FILENAME, detect_types=sqlite.PARSE_DECLTYPES)

    result = None

    with database:
        cur = database.execute("SELECT tweet_index, reblog_id, blogname FROM tweets WHERE tweet_id = ?", [tweet_id])
        result = cur.fetchone()

    database.close()

    return result


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

    result: Optional[Tuple[Person]] = None

    with database:
        # We need to pass the arguments as something with a length, so that the
        # number of question marks can be matched with that length, wo we pass
        # twitter_id as a list of length 1
        cur = database.execute("SELECT person FROM twitter_names WHERE twitter_id = ?", [twitter_id])
        result = cur.fetchone()

    database.close()

    # Just like we needed to pass the arguments as something with length, the
    # database always returns a tuple, so we need to take the first element of
    # that tuple to get the actual person
    return result[0] if result is not None else None
