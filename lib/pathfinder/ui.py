from textual.app import App
from textual.widgets import TextLog, Header, Input
from textual.message import Message
from lib.pathfinder.commander import MasterCommander
import logging
from logging import Handler
import sys

class Prompt(Input):

    def __init__(self, *args, **kwargs):
        self.history = []
        self.history_marker = -1
        return super().__init__(*args, **kwargs)

    class Submitted(Message):
        def __init__(self, sender, user_input):
            self.user_input = user_input
            super().__init__(sender)

    async def on_key(self, event):
        if event.key == 'enter':
            await self.emit(self.Submitted(self, self.value))
            self.history.append(self.value)
            self.history_marker = -1
            self.value = ""
            event.stop()

        if event.key == 'up':
            try:
                self.value = self.history[self.history_marker]
                self.history_marker -= 1
            except IndexError:
                pass  # End of history reached
        if event.key == 'down':
            if self.history_marker < -1:
                self.history_marker += 1
                self.value = self.history[self.history_marker]




class TerminalHandler(Handler):
    def __init__(self, terminal, level=logging.DEBUG):
        self.terminal = terminal
        super().__init__(level)

    def emit(self, record) -> None:
        # TODO: could make a real formatter class here
        style = {
            logging.DEBUG: '[blue]',
            logging.INFO: '[default]',
            logging.WARNING: '[yellow]:warning: ',
            logging.ERROR: '[bold red]',
            logging.CRITICAL: '[blink bold red]'
        }
        log_msg = style[record.levelno]
        log_msg += record.msg + "[/]"
        self.terminal.write(log_msg)


class Terminal(TextLog):

    def on_mount(self):
        logging.getLogger('root').addHandler(TerminalHandler(self))


