import os
import logging
from typing import Optional, Tuple, TypeAlias, Union
from pytumblr2 import TumblrRestClient as TumblrApi
import re
from hopperbot.renderer import Renderer
from hopperbot.twitter_update import TwitterRenderable
from abc import ABC, abstractclassmethod

ContentBlock: TypeAlias = dict[str, Union[str, dict[str, str], list[dict[str, Union[str, int]]]]]

urllib_logger = logging.getLogger("urllib3")
urllib_logger.setLevel(logging.INFO)

oauth_logger = logging.getLogger("oauthlib")
oauth_logger.setLevel(logging.INFO)

requests_logger = logging.getLogger("requests_oauthlib")
requests_logger.setLevel(logging.INFO)

logger = logging.getLogger("Tumblr")
logger.setLevel(logging.DEBUG)


class Renderable(ABC):
    @abstractclassmethod
    def render(self, renderer: Renderer) -> dict[str, str]:
        return {}


class TumblrPost:
    def __init__(
        self,
        content: list[ContentBlock] = [],
        renderables: list[Renderable] = [],
        media_sources: dict[str, str] = {},
        tags: list[str] = [],
        reblog: Optional[Tuple[int, str]] = None,
    ) -> None:
        self.content = content
        self.renderables = renderables
        self.media_sources = media_sources
        self.tags = tags
        self.reblog = reblog

    def add_text_block(self, text: str) -> None:
        self.content.append({
            "type": "text",
            "text": text,
        })

    def add_image_block(self, source: str, alt_text: Optional[str] = None, attribution: Optional[str] = None) -> None:
        block: ContentBlock
        if re.fullmatch("https://64.media.tumblr.com/*", source):
            block = {
                "type": "image",
                "media": {
                    "url": source
                }
            }
            self.content.append(block)
        else:
            block = {
                "type": "image",
                "media": [
                    {
                        "type": "image/png",
                        "identifier": source,
                    }
                ]
            }

        if alt_text:
            block["alt_text"] = alt_text

        if attribution is None:
            self.content.append(block)
        elif re.fullmatch("https://twitter.com/*/status/*", attribution):
            block["attribution"] = {
                "type": "app",
                "url": attribution,
                "app_name": "twitter",
                "display_text": "View on Twitter",
            }
            self.content.append(block)
        else:
            block["attribution"] = {
                "type": "link",
                "url": attribution,
            }
            self.content.append(block)

    def add_link_block(self) -> None:
        raise NotImplementedError

    def add_audio_block(self) -> None:
        raise NotImplementedError

    def add_video_block(self, url: str) -> None:
        block: ContentBlock = {
            "type": "video",
            "url": url,
        }
        if "youtube.com" in url:
            block["provider"] = "youtube"
        elif "twitch.tv" in url:
            raise NotImplementedError
        else:
            # TODO: implement uploading logic
            raise NotImplementedError

        self.content.append(block)

    def add_tweets(self, url: str, alt_texts: list[str], thread: range):
        if not len(alt_texts) == len(thread):
            raise ValueError("All tweets should have an alt text")

        start = len(self.content)
        image_ids = [f"image{index}" for index in range(start, start + len(thread))]
        renderable = TwitterRenderable(url, thread, image_ids, f"tweet-{str(start)}-")
        self.renderables.append(renderable)

        last_image_id = image_ids.pop()
        last_alt_text = alt_texts.pop()

        for image_id, alt_text in zip(image_ids, alt_texts):
            self.add_image_block(image_id, alt_text)

        self.add_image_block(last_image_id, last_alt_text, url)

    def post(self, blogname: str, api: TumblrApi) -> None:
        # Render the images
        renderer = Renderer()
        for renderable in self.renderables:
            media_sources = renderable.render(renderer)
            self.media_sources = self.media_sources | media_sources

        # Post the post
        kwargs = {
            "blogname": blogname,
            "content": self.content,
            "tags": ["hb.automated"],
            "media_sources": self.media_sources,
        }

        if self.reblog is None:
            response = api.create_post(**kwargs)
        else:
            kwargs["parent_blogname"] = self.reblog[0]
            kwargs["id"] = self.reblog[1]
            response = api.reblog_post(**kwargs)

        print(response)

        # Clean up the rendered images
        for filename in self.media_sources.values():
            if os.path.exists(filename):
                os.remove(filename)
            else:
                logger.warning(f"The following filename could not be deleted: {filename}")

        # Add to the tweet database
        raise NotImplementedError("Post should have to be added to tweet database, but this is not implemented yet")

    def __str__(self) -> str:
        return f"Tumlbrpost with {len(self.content)} content blocks"
