import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, TypeAlias, Union
from pytumblr2 import TumblrRestClient
from hopperbot.updates import Update

ContentBlock: TypeAlias = dict[str, Union[str, dict[str, str], List[dict[str, str]]]]

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class App(Enum):
    Twitter = 1

    def __str__(self) -> str:
        return self.name


@dataclass
class Attribution:
    url: str
    app: App


class TumblrPost:
    def __init__(
        self,
        blogname: str,
        content: List[ContentBlock],
        tags: List[str],
        media_sources: Optional[Dict[str, str]] = None,
        reblog: Optional[Tuple[int, str]] = None,
    ) -> None:
        self.blogname = blogname
        self.content = content
        self.tags = tags
        self.media_sources = media_sources
        self.reblog = reblog


class TumblrApi(TumblrRestClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def post_update(self, update: Update, **kwargs) -> None:
        logger.info(f'[Tumblr] Processing task "{str(update)}"')

        post = await update.process(**kwargs)

        if post.reblog is None:
            response = self.create_post(
                blogname=post.blogname,
                content=post.content,
                tags=post.tags,
                media_sources=post.media_sources,
            )
        else:
            (reblog_id, parent_blogname) = post.reblog
            response = self.reblog_post(
                blogname=post.blogname,
                parent_blogname=parent_blogname,
                id=reblog_id,
                content=post.content,
                tags=post.tags,
                media_sources=post.media_sources,
            )

        if "meta" in response:
            logger.error(f"[Tumblr] {response}")
        else:
            logger.info(f"[Tumblr] Posted task {str(update)} ({response})")

            tumblr_id = response.get("id")

            if tumblr_id is None:
                logger.error("Error")
            else:
                update.cleanup(tumblr_id)


def image_block(identifier: str, alt_text: str, url: Optional[str] = None) -> ContentBlock:
    block: ContentBlock = {
        "type": "image",
        "media": [
            {
                "type": "image/png",
                "identifier": identifier,
            }
        ],
        "alt_text": alt_text,
    }

    if url is None:
        return block
    elif "twitter.com" in url:
        block["attribution"] = {
            "type": "app",
            "url": url,
            "app_name": "twitter",
            "display_text": "View on Twitter",
        }
        return block
    else:
        block["attribution"] = {
            "type": "link",
            "url": url,
        }
        return block


def text_block(text: str) -> ContentBlock:
    return {
        "type": "text",
        "text": text,
    }
