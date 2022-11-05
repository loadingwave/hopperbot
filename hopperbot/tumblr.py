import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple, TypeAlias, Union
from pytumblr2 import TumblrRestClient

ContentBlock: TypeAlias = dict[str, Union[str, dict[str, str], list[dict[str, Union[str, int]]]]]

urllib_logger = logging.getLogger("urllib3")
urllib_logger.setLevel(logging.INFO)

oauth_logger = logging.getLogger("oauthlib")
oauth_logger.setLevel(logging.INFO)

requests_logger = logging.getLogger("requests_oauthlib")
requests_logger.setLevel(logging.INFO)

logger = logging.getLogger("Tumblr")
logger.setLevel(logging.DEBUG)


class TumblrPost:
    def __init__(
        self,
        blogname: str,
        content: list[ContentBlock],
        tags: list[str],
        media_sources: Optional[dict[str, str]] = None,
        reblog: Optional[Tuple[int, str]] = None,
    ) -> None:
        self.blogname = blogname
        self.content = content
        self.tags = tags
        self.media_sources = media_sources
        self.reblog = reblog


class Update(ABC):
    @abstractmethod
    async def process(self) -> TumblrPost:
        pass

    @abstractmethod
    def cleanup(self, tumblr_id: int) -> None:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass


class TumblrApi(TumblrRestClient):
    def __init__(self, **kwargs: str) -> None:
        super().__init__(**kwargs)
        logger.info("Initialized TumblrApi")

    async def post_update(self, update: Update) -> None:
        logger.debug(f'Processing update "{str(update)}"')

        post = await update.process()

        logger.debug(f'Got post for update "{str(update)}"')

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
            logger.error(f"Something went wrong posting update {str(update)}:")
            logger.error(f"{response}")
        else:
            logger.info(f"Posted update {str(update)}")
            logger.debug(f"response: {response}")

            tumblr_id = response.get("id")

            if tumblr_id is None:
                logger.error(f"Update {str(update)} did not return a tumblr id (no cleanup done)")
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
