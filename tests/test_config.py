from hopperbot.config import init_twitter_blognames


def test_simple_good_config():
    genrated_dict = init_twitter_blognames("tests/simple_good_config.toml")

    correct_dict = {
        "space_stew": "test37",
        "tapwaterthomas": "test37"
    }

    assert genrated_dict == correct_dict


def test_mixed_case_config():
    genrated_dict = init_twitter_blognames("tests/mixed_case_config.toml")

    correct_dict = {
        "space_stew": "test37",
        "tapwaterthomas": "test37"
    }

    assert genrated_dict == correct_dict


def test_no_update_config():
    genrated_dict = init_twitter_blognames("tests/no_update_config.toml")

    correct_dict = {}

    assert genrated_dict == correct_dict


def test_no_twitter_config():
    genrated_dict = init_twitter_blognames("tests/no_twitter_config.toml")

    correct_dict = {}

    assert genrated_dict == correct_dict
