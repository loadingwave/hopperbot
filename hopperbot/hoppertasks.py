from typing import List, TypeAlias, Union

ContentBlock: TypeAlias = dict[str, Union[str, dict[str, str], List[dict[str, str]]]]


class HopperTask:
    def __init__(self, content: List[ContentBlock]) -> None:
        self.content = content


class TwitterTask(HopperTask):
    def __init__(
        self,
        content: List[ContentBlock],
        url: str,
        filename_prefix: str,
        tweet_index: int,
        thread_height: int,
    ) -> None:
        self.url = url
        self.filename_prefix = filename_prefix
        self.tweet_index = tweet_index
        self.thread_height = thread_height
        super().__init__(content)
