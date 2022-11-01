from typing import List, TypeAlias, Union

ContentBlock: TypeAlias = dict[str, Union[str, dict[str, str], List[dict[str, str]]]]


class Update:
    def __init__(self, content: List[ContentBlock], identifier: str) -> None:
        self.content = content
        self.identifier = identifier


class TwitterUpdate(Update):
    def __init__(
        self,
        content: List[ContentBlock],
        url: str,
        identifier: str,
        tweet_index: int,
        thread_height: int,
    ) -> None:
        self.url = url
        self.tweet_index = tweet_index
        self.thread_height = thread_height
        super().__init__(content, identifier)
