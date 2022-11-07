from hopperbot.database import Database
from hopperbot.people import HE, THEY, Person
import pytest
import os


@pytest.fixture
def setup():
    filename = "test.db"
    os.remove(filename)
    return Database(filename)


def test_add_get_tweet(setup: Database):
    tweet_id = 1587931744677744640
    tweet_index = 1
    tumblr_id = 699848368965533696
    blogname = "test37"
    setup.add_tweet(tweet_id, tweet_index, tumblr_id, blogname)

    result = setup.get_tweet(tweet_id)

    assert result == (tweet_index, tumblr_id, blogname)


def test_add_get_person(setup: Database):
    person = Person("Thomas", [HE, THEY])
    twitter_id = 1478064563358740481

    setup.add_person(twitter_id, person)

    result = setup.get_person(twitter_id)

    assert result == person
