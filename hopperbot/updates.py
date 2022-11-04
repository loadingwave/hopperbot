from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, TypeAlias, Union

ContentBlock: TypeAlias = dict[str, Union[str, dict[str, str], List[dict[str, str]]]]


class TumblrPost:
    def __init__(
        self,
        blogname: str,
        content: List[ContentBlock],
        tags: List[str],
        media_sources: Union[None, Dict[str, str]],
        reblog: Union[None, Tuple[int, str]],
    ) -> None:
        self.blogname = blogname
        self.content = content
        self.tags = tags
        self.media_sources = media_sources
        self.reblog = reblog


class Update(ABC):
    # Using "type: ignore" for **kwargs
    @abstractmethod
    async def process(self, **kwargs) -> TumblrPost:  # type: ignore
        pass

    @abstractmethod
    def cleanup(self) -> None:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass
