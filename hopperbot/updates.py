from abc import ABC, abstractmethod
from hopperbot.tumblr import TumblrPost


class Update(ABC):
    # Using "type: ignore" for **kwargs
    @abstractmethod
    async def process(self, **kwargs) -> TumblrPost:  # type: ignore
        pass

    @abstractmethod
    def cleanup(self, tumblr_id: int) -> None:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass
