import sqlite3 as sqlite
from enum import Enum
from typing import List, Type

PRONOUNS = [
    ["he", "him", "his", "his", "himself"],
    ["she", "her", "her", "hers", "herself"],
    ["they", "them", "their", "theirs", "themselves"],
    ["xey", "xem", "xyr", "xyrs", "xemself"],
    ["star", "star", "stars", "stars", "starself"],
    ["it", "it", "its", "its", "itself"],
]


class Context(Enum):
    subject = (0,)
    object = (1,)
    possessive_adj = (2,)
    possessive = (3,)
    reflexive = (4,)


class Pronouns(Enum):
    he = (["he", "him", "his", "his", "himself"],)
    she = (["she", "her", "her", "hers", "herself"],)
    they = (["they", "them", "their", "theirs", "themselves"],)
    xey = (["xey", "xem", "xyr", "xyrs", "xemself"],)
    star = (["star", "star", "stars", "stars", "starself"],)
    it = ["it", "it", "its", "its", "itself"]

    def format(self, context: Context) -> str:
        return self.value[context.value]


class Person:
    def __init__(self, name: str, pronouns: List[Pronouns]) -> None:
        self.name = name
        self.pronouns = pronouns

    def __conform__(self, protocol: Type[sqlite.PrepareProtocol]) -> str:
        if protocol is sqlite.PrepareProtocol:
            result = self.name
            for pronoun in self.pronouns:
                result += f";{pronoun}"
            return result
        else:
            return ""


def main() -> None:
    con = sqlite.connect("test.db")

    # tweet_id reblog_id thread_index

    me = Person("Thomas", [Pronouns.he])
    tommy = Person("Tommy", [Pronouns.he])

    data = [(1, me), (2, tommy)]
    with con:
        con.executemany("INSERT INTO tweets(tweet_id, people) VALUES(?, ?)", data)

    for row in con.execute("SELECT tweet_id, people FROM tweets"):
        print(row)


if __name__ == "__main__":
    main()
