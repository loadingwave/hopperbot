from datetime import datetime
from typing import Union, cast

import xmltodict
from aiohttp import web


def parse_feed(source: str) -> tuple[str, str, bool]:
    xml = xmltodict.parse(source)

    feed = xml.get("feed")
    if feed is None:
        raise ValueError("No feed found in xml")
    feed = cast(dict[str, Union[str, dict[str, Union[str, dict[str, str]]]]], feed)

    entry = feed.get("entry")
    if entry is None:
        raise ValueError("No entry found in xml")
    entry = cast(dict[str, Union[str, dict[str, str]]], entry)

    time_format = "%Y-%m-%dT%H:%M:%S%z"

    published_str = cast(str | None, entry.get("published"))
    if published_str is None:
        raise ValueError("No published found in xml")
    published_time = datetime.strptime(published_str, time_format)

    updated_str = cast(str | None, entry.get("updated"))
    if updated_str is None:
        raise ValueError("No updated found in xml")
    updated_str = updated_str[:19] + updated_str[-6:]
    updated_time = datetime.strptime(updated_str, time_format)

    new_video = (updated_time - published_time).seconds == 0

    url_element = entry.get("link")
    if url_element is None:
        raise ValueError("No url found in xml")

    url_element = cast(dict[str, str], url_element)
    url = cast(str | None, url_element.get("@href"))
    if url is None:
        raise ValueError("No url found in xml")

    channel_id = entry.get("yt:channelId")
    if channel_id is None:
        raise ValueError("No channel_id found in xml")
    channel_id = cast(str, channel_id)

    return (channel_id, url, new_video)


async def print_post(request: web.Request) -> web.Response:
    if request.content_type == "application/atom+xml":
        feed_str = await request.text()
        (channel_id, url, new_video) = parse_feed(feed_str)
        action = "posted a new video" if new_video else "updated this video"
        print(f"Channel {channel_id} {action} ({url})")

    return web.Response(status=204)


class Youtube:

    app: web.Application
    runner: web.AppRunner

    def __init__(self):
        app = web.Application()
        app.add_routes([web.post("/", print_post)])

    async def setup(self):
        self.runner = web.AppRunner(self.app)
        raise NotImplementedError
