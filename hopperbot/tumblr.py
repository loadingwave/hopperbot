import logging
import os
import re
from abc import ABC, abstractclassmethod
from typing import Any, Optional, Tuple, TypeAlias, Union

from pytumblr2 import TumblrRestClient as TumblrApi

from hopperbot.renderer import Renderer

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
        identifier: Optional[str] = None,
        content: list[ContentBlock] = [],
        renderables: list[Renderable] = [],
        media_sources: dict[str, str] = {},
        tags: list[str] = [],
        reblog: Optional[Tuple[int, str]] = None,
    ) -> None:
        self.identifier = identifier
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

    def add_tag(self, tag: str) -> None:
        self.tags.append("tag")

    async def post(self, blogname: str, api: TumblrApi) -> dict[str, Any]:
        # Render the images
        renderer = Renderer()
        for renderable in self.renderables:
            media_sources = renderable.render(renderer)
            self.media_sources = self.media_sources | media_sources

        # Post the post. We need to copy the media_sources because the api consumes the dictionary
        # and these structures are internaly mutable
        kwargs = {
            "blogname": blogname,
            "content": self.content,
            "tags": self.tags,
            "media_sources": self.media_sources.copy(),
        }

        if self.reblog is None:
            response = api.create_post(**kwargs)
        else:
            kwargs["id"] = str(self.reblog[0])
            kwargs["parent_blogname"] = self.reblog[1]
            response = api.reblog_post(**kwargs)

        # Log posting success
        if response.get("state") == "published":
            logger.info(f"Sucessfully posted to {blogname}")

        # Clean up the rendered images
        for filename in self.media_sources.values():
            if os.path.exists(filename):
                os.remove(filename)
            else:
                logger.warning(f"The following filename could not be deleted: {filename}")

        return response

    def __str__(self) -> str:
        return f"""Content: {self.content}
Media Sources: {self.media_sources}
Tags: {self.tags}
        """
