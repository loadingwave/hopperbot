from hopperbot.renderer import Renderer
from selenium.common.exceptions import NoSuchElementException
import pytest


@pytest.fixture
def renderer() -> Renderer:
    return Renderer()


def test_single_tweet(renderer: Renderer) -> None:
    url = "https://twitter.com/space_stew/status/1587931744677744640"
    filename_prefix = "tests/test_single_tweet"
    filenames = renderer.render_tweets(url, filename_prefix, range(0, 1))

    assert len(filenames) == 1
    for filename in filenames:
        print(f"Check manually if {filename} is rendered correctly")


def test_sinlge_reply(renderer: Renderer) -> None:
    url = "https://twitter.com/space_stew/status/1587931814156722178"
    filename_prefix = "test/test_sinlge_reply"
    filenames = renderer.render_tweets(url, filename_prefix, range(1, 2))

    assert len(filenames) == 1
    for filename in filenames:
        print(f"Check manually if {filename} is rendered correctly")


def test_two_tweets(renderer: Renderer) -> None:
    url = "https://twitter.com/space_stew/status/1587931814156722178"
    filename_prefix = "tests/test_two_tweets"
    filenames = renderer.render_tweets(url, filename_prefix, range(0, 2))

    assert len(filenames) == 2
    for filename in filenames:
        print(f"Check manually if {filename} is rendered correctly")


def test_incorrect_range_start(renderer: Renderer) -> None:
    url = "https://twitter.com/space_stew/status/1588854790817165312"
    filename_prefix = "tests/test_incorrect_range_start"

    with pytest.raises(ValueError) as e:
        renderer.render_tweets(url, filename_prefix, range(-1, 1))

    assert str(e.value) == "Thread range should have positive start"


def test_incorrect_range_step(renderer: Renderer) -> None:
    url = "https://twitter.com/space_stew/status/1588854790817165312"
    filename_prefix = "tests/test_incorrect_range_step"

    with pytest.raises(ValueError) as e:
        renderer.render_tweets(url, filename_prefix, range(4, 0, -1))

    assert str(e.value) == "Thread range should have positive step"


def test_incorrect_range_stop(renderer: Renderer) -> None:
    url = "https://twitter.com/space_stew/status/1588854790817165312"
    filename_prefix = "tests/test_incorrect_range_step"

    with pytest.raises(NoSuchElementException):
        renderer.render_tweets(url, filename_prefix, range(1, 2))
