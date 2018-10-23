from abc import ABC, abstractmethod
from argparse import Namespace, ArgumentParser
from darty.output_writer import AbstractOutputWriter


class AbstractCommand(ABC):

    """Abstract class to implement a command"""

    def __init__(self):
        """Command's constructor

        Raises:
            ValueError: If command's arguments can't be processed.
        """

    @staticmethod
    @abstractmethod
    def get_command_name() -> str:
        """Returns a sub-command name."""
        pass

    @staticmethod
    @abstractmethod
    def get_description() -> str:
        """Returns a sub-command description."""
        pass

    def configure(self, subparser: ArgumentParser):
        """Adds arguments to the parser."""
        pass

    @abstractmethod
    def run(self, args: Namespace, settings: dict, output: AbstractOutputWriter) -> bool:
        """Performs a command
        Returns:
            bool: True for success, False otherwise.
        Raises:
            ValueError: If command's arguments can't be processed.
        """
        return True
