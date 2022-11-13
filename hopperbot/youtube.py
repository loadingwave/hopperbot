from datetime import datetime
from typing import Union, cast

import xmltodict
from aiohttp import web

from hopperbot.tumblr import Update, TumblrPost, text_block, video_block


async def handle(request: web.Request):
    name = request.match_info.get("name", "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)


class YoutubeUpdate(Update):
    def __init__(self, channel_id: str, url: str) -> None:
        self.channel_id = channel_id
        self.url = url


def youtube_update(channel_id: str, url: str) -> TumblrPost:
    header = text_block("Name posted on youtube!")
    yt_block = video_block("https://www.youtube.com/watch?v=MCKeXhta3H0")
    return TumblrPost("test37", [header, yt_block], tags=[])


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

    diff = updated_time - published_time

    new_video = diff.seconds == 0

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


app = web.Application()
app.add_routes([web.get("/", handle), web.get("/{name}", handle), web.post("/", print_post)])

if __name__ == "__main__":
    web.run_app(app)
