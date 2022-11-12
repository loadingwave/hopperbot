import os

import pytest

from hopperbot.database import Database
from hopperbot.people import HE, THEY, Person


@pytest.fixture
def database() -> Database:
    filename = "test_twitter_update.db"
    path = os.path.join("tests", filename)
    if os.path.exists(path):
        os.remove(path)
    database = Database(filename)
    database.add_person(1478064563358740481, Person("Thomas", [HE]))
    database.add_person(785517623626887169, Person("Thomas", [HE]))
    database.add_person(1344189615134003201, Person("Ranboo", [HE, THEY]))
    # Add 1 tweet
    database.add_tweet(1588854790817165312, 0, 700079130352435200, "test37")
    database.add_tweet(1587936832997953536, 0, 699849641537224704, "test37")
    return database
