
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
