from typing import List, TypeAlias, Union

ContentBlock: TypeAlias = dict[str, Union[str, dict[str, str], List[dict[str, str]]]]


class Update:
    def __init__(self, content: List[ContentBlock], identifier: Union[int, str], reblog_key: Union[None, int]) -> None:
        self.content = content
        self.identifier = identifier
        self.reblog_key = reblog_key
