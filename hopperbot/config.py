import logging
from typing import Union, cast

import tomllib

TWITTER_BLOGNAMES: dict[str, str] = {}

logger = logging.getLogger("config")


def init_twitter_blognames(filename: str) -> dict[str, str]:
    with open(filename, "rb") as f:
        data: dict[str, list[dict[str, Union[str, list[dict[str, str]]]]]] = tomllib.load(f)

    if data is None:
        raise Exception("Reading config returned None")
    else:
        twitter_blognames = {
            k: v
            for d in [
                {
                    cast(str, twitter_update.get("username")).lower(): cast(str, update.get("blogname"))
                    for twitter_update in cast(list[dict[str, str]], update.get("Twitter", []))
                }
                for update in data.get("Update", [])
            ]
            for k, v in d.items()
        }
        logger.debug(f"Initalized twitter_blognames: {twitter_blognames}")

        global TWITTER_BLOGNAMES
        TWITTER_BLOGNAMES = twitter_blognames

        return twitter_blognames
