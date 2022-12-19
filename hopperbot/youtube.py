import logging
from asyncio import Queue
from datetime import datetime
from typing import Optional

import xmltodict
from aiohttp import web

from hopperbot.errors import Err, Ok, Result
from hopperbot.tumblr import TumblrPost

logger = logging.getLogger("Youtube")
logger.setLevel(logging.DEBUG)


class Youtube:

    app: web.Application
    runner: web.AppRunner
    queue: Queue

    def __init__(self):
        app = web.Application()
        app.add_routes([web.post("/", self.handle_youtube_notification)])
        raise NotImplementedError

    async def setup(self):
        self.runner = web.AppRunner(self.app)
        raise NotImplementedError

    def xml_to_post(self, xml_string: str) -> Result[Optional[TumblrPost], KeyError]:
        xml = xmltodict.parse(xml_string)

        try:
            data = xml["feed"]["entry"]
            publish_time_str: str = data["published"]
            update_time_str: str = data["updated"]
            url = data["link"]["@href"]
            channel_name = data["author"]["name"]
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
            post = TumblrPost()
            post.add_text_block(f"{channel_name} uploaded!")
            post.add_video_block(url)
            logger.info(f"This Youtube video was just uploaded: {url}")
            return Ok(post)
        else:
            logger.info(f"This Youtube video was just updated: {url}")
            return Ok(None)

    async def handle_youtube_notification(self, request: web.Request) -> web.Response:
        if request.content_type == "application/atom+xml":
            xml_string = await request.text()

            match self.xml_to_post(xml_string):
                case Err(e):
                    logger.error(f"Error while parsing a Youtube notification: {e}")
                case Ok(None):
                    pass
                case Ok(post):
                    await self.queue.put(post)
        else:
            logger.warning(f'Youtube was just asked to handle "{request.content_type}" instead of "application/atom+xml"')

        return web.Response(status=204)
