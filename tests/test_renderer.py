from hopperbot.renderer import Renderer
import pytest


@pytest.fixture
def renderer() -> Renderer:
    return Renderer()


def test_single_tweet(renderer: Renderer) -> None:
    url = "https://twitter.com/space_stew/status/1587931744677744640"
    filename_prefix = "test_single_tweet"
    filenames = renderer.render_tweets(url, filename_prefix, range(0, 1))

    assert len(filenames) == 1
    for filename in filenames:
        print(f"Check manually if {filename} is rendered correctly")


def test_sinlge_reply(renderer: Renderer) -> None:
    url = "https://twitter.com/space_stew/status/1587931814156722178"
    filename_prefix = "test_sinlge_reply"
    filenames = renderer.render_tweets(url, filename_prefix, range(1, 2))

    assert len(filenames) == 1
    for filename in filenames:
        print(f"Check manually if {filename} is rendered correctly")


def test_two_tweets(renderer: Renderer) -> None:
    url = "https://twitter.com/space_stew/status/1587931814156722178"
    filename_prefix = "test_two_tweets"
    filenames = renderer.render_tweets(url, filename_prefix, range(0, 2))

    assert len(filenames) == 2
    for filename in filenames:
        print(f"Check manually if {filename} is rendered correctly")
