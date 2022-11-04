import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, TypeAlias, Union

ContentBlock: TypeAlias = dict[str, Union[str, dict[str, str], List[dict[str, str]]]]

logger = logging.getLogger(__name__)


@dataclass
class Reblog:
    blogname: str
    id: int


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
