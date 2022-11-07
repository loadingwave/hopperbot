from hopperbot.database import Database
from hopperbot.people import HE, THEY, Person
import pytest
import os


@pytest.fixture
def database() -> Database:
    filename = "test.db"
    os.remove(filename)
    return Database(filename)


def test_add_get_tweet(database: Database):
    tweet_id = 1587931744677744640
    tweet_index = 1
    tumblr_id = 699848368965533696
    blogname = "test37"
    database.add_tweet(tweet_id, tweet_index, tumblr_id, blogname)

    result = database.get_tweet(tweet_id)

    assert result == (tweet_index, tumblr_id, blogname)


def test_get_nonexistant_tweet(database: Database):
    not_tweet_id = 1
    result = database.get_tweet(not_tweet_id)

    assert result is None


def test_add_get_person(database: Database):
    person = Person("Thomas", [HE, THEY])
    twitter_id = 1478064563358740481

    database.add_person(twitter_id, person)

    result = database.get_person(twitter_id)

    assert result == person


def test_get_nonexistant_person(database: Database):
    not_twitter_id = 1
    result = database.get_person(not_twitter_id)

    assert result is None
