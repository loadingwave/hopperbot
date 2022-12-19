from asyncio import Queue
from datetime import datetime
from typing import Optional

import xmltodict
from aiohttp import web

from hopperbot.errors import Err, Ok, Result
from hopperbot.tumblr import TumblrPost


def xml_to_post(xml_string: str) -> Result[Optional[TumblrPost], KeyError]:
    xml = xmltodict.parse(xml_string)

    try:
        data = xml["feed"]["entry"]
        publish_time_str: str = data["published"]
        update_time_str: str = data["updated"]
    except KeyError as e:
        return Err(e)

    # Compare publish and update times to determine if this is a new video
    time_format = "%Y-%m-%dT%H:%M:%S%z"
    publish_time_str = publish_time_str[:19] + publish_time_str[-6:]
    publish_time = datetime.strptime(publish_time_str, time_format)

    update_time_str = update_time_str[:19] + update_time_str[-6:]
    update_time = datetime.strptime(publish_time_str, time_format)

    new_video = (update_time - publish_time).seconds == 0

    # Prepare the post
    if new_video:
        try:
            channel_name = data["author"]["name"]
            url = data["link"]["@href"]
        except KeyError as e:
            return Err(e)

        post = TumblrPost()
        post.add_text_block(f"{channel_name} uploaded!")
        post.add_video_block(url)
        return Ok(post)
    else:
        return Ok(None)


async def handle_youtube_notification(request: web.Request) -> web.Response:
    if request.content_type == "application/atom+xml":
        xml_string = await request.text()
        post = xml_to_post(xml_string)

        if post is not None:
            queue = Queue()
            await queue.put(post)
            raise NotImplementedError

    return web.Response(status=204)


class Youtube:

    app: web.Application
    runner: web.AppRunner

    def __init__(self):
        app = web.Application()
        app.add_routes([web.post("/", handle_youtube_notification)])
        raise NotImplementedError

    async def setup(self):
        self.runner = web.AppRunner(self.app)
        raise NotImplementedError
