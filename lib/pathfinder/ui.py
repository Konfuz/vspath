from textual.app import App
from textual.widgets import TextLog, Header, Input
from textual.message import Message
from logging import Handler
from lib.pathfinder.commander import MasterCommander
import sys

class Prompt(Input):

    class Submitted(Message):
        def __init__(self, sender, user_input):
            self.user_input = user_input
            super().__init__(sender)

    async def on_key(self, event):
        if event.key == 'enter':
            await self.emit(self.Submitted(self, self.value))
            self.value = ""
            event.stop()


class Terminal(TextLog, Handler):

    def emit(self, message: Message) -> bool:
        self.write(message)

