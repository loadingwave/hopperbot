from tweepy.asynchronous import AsyncStreamingClient
from tweepy import Response
import logging


class TwitterListener(AsyncStreamingClient):
    def __init__(self, bearer_token: str) -> None:
        super().__init__(bearer_token)

    async def on_connect(self) -> None:
        logging.info("TwitterListener is connected")

    async def on_response(self, response: Response) -> None:
        print("[Twitter]", response)
