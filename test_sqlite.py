import sqlite3 as sqlite
from pprint import pprint

from pytumblr2 import TumblrRestClient as TumblrClient

from hopperbot.people import HE, THEY, Person, adapt_person, convert_person
from hopperbot.secrets import tumblr_keys


def sql_main() -> None:

    sqlite.register_adapter(Person, adapt_person)
    sqlite.register_converter("PERSON", convert_person)

    con = sqlite.connect("tweets.db", detect_types=sqlite.PARSE_DECLTYPES)
    con.execute(
        "CREATE TABLE tweets(tweet_id INTEGER PRIMARY KEY, reblog_key INTEGER, thread_index INTEGER, person PERSON)"
    )
    tweet_id = 1587818261349302272
    reblog_key = 699819997977100288
    thread_index = 1
    ranboo = Person("Ranboo", [HE, THEY])

    with con:
        con.execute(
            "INSERT INTO tweets(tweet_id, reblog_key, thread_index, person) VALUES(?, ?, ?, ?)",
            (tweet_id, reblog_key, thread_index, ranboo),
        )

    id: int
    person: Person

    for response in con.execute("SELECT tweet_id, reblog_key, thread_index, person FROM tweets"):
        print(response)


def tumblr_main() -> None:
    tumblr_client = TumblrClient(**tumblr_keys)

    response = tumblr_client.create_post(
        blogname="test37", content=[{"type": "text", "text": "TEST :D"}], tags=["hb.test"]
    )

    pprint(response)


if __name__ == "__main__":
    tumblr_main()
