import sqlite3 as sqlite
from hopperbot.people import Person, adapt_person, convert_person


def main() -> None:

    sqlite.register_adapter(Person, adapt_person)
    sqlite.register_converter("person", convert_person)

    con = sqlite.connect("test.db", detect_types=sqlite.PARSE_DECLTYPES)
    # con.execute("CREATE TABLE tweets(id INTEGER PRIMARY KEY, person person)")

    # # tweet_id reblog_id thread_index

    # me = Person("Thomas", [pn.HE, pn.THEY])
    # tommy = Person("Tommy", [pn.HE])

    # data = [(1, me), (2, tommy)]
    # with con:
    #     con.executemany("INSERT INTO tweets(id, person) VALUES(?, ?)", data)

    id: int
    person: Person

    for (id, person) in con.execute("SELECT id, person FROM tweets"):
        print(f"id: {id}, random pronoun: {person.em()}")


if __name__ == "__main__":
    main()
