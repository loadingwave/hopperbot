import sqlite3 as sqlite
from hopperbot.pronouns import Pronoun
import hopperbot.pronouns as pn
from typing import List


class Person:
    def __init__(self, name: str, pronouns: List[Pronoun]) -> None:
        self.name = name
        self.pronouns = pronouns


def main() -> None:
    con = sqlite.connect("test.db")

    # tweet_id reblog_id thread_index

    me = Person("Thomas", [pn.HE])
    tommy = Person("Tommy", [pn.HE])

    data = [(1, me), (2, tommy)]
    with con:
        con.executemany("INSERT INTO tweets(tweet_id, people) VALUES(?, ?)", data)

    for row in con.execute("SELECT tweet_id, people FROM tweets"):
        print(row)


if __name__ == "__main__":
    main()
