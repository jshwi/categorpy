import argparse


class Parser(argparse.ArgumentParser):
    def __init__(self):
        super().__init__()
        self.args: argparse.Namespace = ...
    def _add_arguments(self) -> None: ...
