import logging
from typing import Optional, Union, cast

import tomllib

TWITTER_BLOGNAMES: dict[str, str | None] = {}

logger = logging.getLogger("hopperbot")


def init_twitter_blognames(filename: str) -> Optional[list[str]]:
    with open(filename, "rb") as f:
        data: dict[str, list[dict[str, Union[str, list[dict[str, str]]]]]] = tomllib.load(f)

    if data is None:
        logger.error("Reading config returned None")
        return None
    else:
        global TWITTER_BLOGNAMES
        TWITTER_BLOGNAMES = {
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
        logger.debug(f"Initalized twitter_blognames: {TWITTER_BLOGNAMES}")

        return list(TWITTER_BLOGNAMES.keys())
