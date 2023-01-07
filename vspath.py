#!/usr/bin/env python3
"""vspath find shortest route between two points."""
import logging
import sys

import graph_tool as gt
from textual.app import App
from textual.widgets import Header

from lib.pathfinder.commander import MasterCommander
from lib.pathfinder.config import config
from lib.pathfinder.ui import Terminal, Prompt

logging.basicConfig(level=logging.DEBUG)


class VSPath(App):
    CSS_PATH = 'config/ui.css'

    def __init__(self):
        super().__init__(watch_css=config.debugmode)
        # Populate Data
        try:
            graph = gt.load_graph(config.data_file)
        except IOError:
            graph = None
            logging.warning('No existing Navgraph found')
        self.commander = MasterCommander(self, graph)

    def compose(self):
        """Compose app-widgets"""
        yield Header(id='header', show_clock=True)
        yield Terminal(id='textlog', highlight=True, markup=True)
        yield Prompt(id='prompt', classes='box')

    def on_prompt_submitted(self, message):
        self.query_one(Terminal).write(message.user_input)
        self.commander.process(message.user_input)

    def action_import_file(self, filename):
        self.commander.graph_commander.do_import(filename)

    def action_closest_traders(self, origin, distance=1000):
        pass


if __name__ == "__main__":
    logging.debug(f"Storing Data under {config.data_file}")

    # import new data
    app = VSPath()
    app.run()

