import logging
from asyncio import Queue

from tweepy import Response, StreamRule, Tweet
from tweepy.asynchronous import AsyncStreamingClient

from hopperbot.tumblr import Update
from hopperbot.twitter_update import TwitterUpdate

tweepy_logger = logging.getLogger("tweepy")
tweepy_logger.setLevel(logging.INFO)

logger = logging.getLogger("Twitter")
logger.setLevel(logging.DEBUG)

TWITTER_RULE_MAX_LEN = 512


class TwitterListener(AsyncStreamingClient):
    def __init__(self, queue: Queue[Update], bearer_token: str) -> None:
        self.queue = queue

        # To be able to follow reblog trails, we need to be able to lookup tweets
        super().__init__(bearer_token)

    async def on_connect(self) -> None:
        logger.info("Twitter Listener is connected")

    async def reset_rules(self) -> None:
        get_response = await self.get_rules()
        if isinstance(get_response, Response):
            data: list[StreamRule]
            (data, _, errors, _) = get_response
            if errors:
                for error in errors:
                    logger.error(f'Trying to get rules returned an error: "{error}"')
            elif data:
                delete_response = await self.delete_rules(data)
                if isinstance(delete_response, Response):
                    if errors:
                        for error in errors:
                            logger.error(f'Trying to delete rules returned an error: "{error}"')
                    else:
                        for rule in data:
                            logger.debug(f'Deleted rule: "{rule.value}"')
                else:
                    logger.error("Trying to delete rules did not return a Response somehow")
        else:
            logger.error("Trying to get rules did not return a Response somehow")

    async def on_response(self, response: Response) -> None:
        tweet: Tweet
        # This is a little while lie, but it is correct when fetching a username
        includes: dict[str, list[dict[str, str]]]
        (tweet, includes, errors, _) = response
        if errors:
            for error in errors:
                logger.error(f"Got send a response, but it contained errors: {error}")
            return

        users = includes.get("users")
        if not users:
            logger.error("Got send a response, but it did not contain users")
            return

        username = users[0].get("username")
        if username is None:
            logger.error("Got send a response, but first included user did not have a username")
            return

        update = TwitterUpdate(username, tweet)

        await self.queue.put(update)
        logger.info(f'Produced update: "{str(update)}: {tweet.text}"')

    async def add_usernames(self, usernames: list[str]) -> None:
        if len(usernames) <= 21:
            rule = StreamRule(" OR ".join(map(lambda x: "from:" + x, usernames)), "rule0")
            response = await self.add_rules(rule)
            if isinstance(response, Response):
                for added_rule in response.data:
                    logger.debug(f'Added rule: "{added_rule.value}"')
            else:
                logger.error("Adding rules did not return a Response somehow")
        else:
            next = usernames.pop()

            # Generate at most 5 rules with as many usernames as possible per rule
            for i in range(5):
                rule = "from:" + next
                next = usernames.pop()

                while next is not None and len(rule) + 9 + len(next) <= TWITTER_RULE_MAX_LEN:
                    rule += " OR from:" + next
                    next = usernames.pop()

                streamrule = StreamRule(rule, f"rule{i}")

                response = await self.add_rules(streamrule)

                if isinstance(response, Response):
                    for added_rule in response.data:
                        logger.debug(f'Added rule: "{added_rule.value}"')
                else:
                    logger.error("Adding rules did not return a Response somehow")

                if next is None:
                    # if there are no more users to add, stop generating rules
                    break

            if len(usernames) > 0:
                logger.error(f"{len(usernames)} usernames did not fit in a rule, so were not added")
