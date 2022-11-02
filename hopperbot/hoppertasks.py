from typing import List, TypeAlias, Union

ContentBlock: TypeAlias = dict[str, Union[str, dict[str, str], List[dict[str, str]]]]


class Update:
    def __init__(self, content: List[ContentBlock], identifier: str) -> None:
        self.content = content
        self.identifier = identifier
