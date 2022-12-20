import sys


class MasterCommander:

    def __init__(self):
        self.commands = {
            'quit': self.do_quit
        }

    def process(self, user_input):
        input = user_input.lower().split()
        try:
            self.commands[input[0]](input[1:])
        except KeyError:
            logging.warning(f"Command {input[0]} is not known.")

    def do_quit(self, _):
        sys.exit(0)
