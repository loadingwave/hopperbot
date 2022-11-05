from hopperbot.database import init_database, FILENAME
from hopperbot.config import twitter_data
import logging
import sys
import sqlite3 as sqlite


def init_logger():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(name)-8s - %(levelname)-8s - %(message)s")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def main():
    init_logger()
    init_database()

    database = sqlite.connect(FILENAME, detect_types=sqlite.PARSE_DECLTYPES)

    with database:
        for (twitter_id, person) in twitter_data.items():
            database.execute(
                "INSERT INTO twitter_names(twitter_id, person) VALUES(?, ?)",
                (twitter_id, person),
            )
            logging.debug(f"Inserted person {person.name} with twitter id: {twitter_id} into twitter names table")

    database.close()

    database = sqlite.connect(FILENAME, detect_types=sqlite.PARSE_DECLTYPES)
    rows = database.execute("SELECT * from twitter_names").fetchall()
    database.close()

    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
