from typing import Generic, TypeVar, NoReturn

OkType = TypeVar("OkType")
ErrType = TypeVar("ErrType", bound=Exception)


class Ok(Generic[OkType]):
    def __init__(self, value: OkType) -> None:
        self._value = value

    def unwrap(self) -> OkType:
        return self._value


class Err(Generic[ErrType]):
    def __init__(self, exception: ErrType) -> None:
        self._exception = exception

    def unwrap(self) -> NoReturn:
        raise self._exception


Result = Ok[OkType] | Err[ErrType]


class HopperbotError(Exception):
    pass


class UnknownPersonError(HopperbotError):
    pass


class TwitterError(HopperbotError):
    pass


class NoTweetError(TwitterError):
    pass


class NoReferencedTweetError(TwitterError):
    pass
