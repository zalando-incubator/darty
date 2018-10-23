import logging
import sys
from abc import ABC, abstractmethod
from contextlib import contextmanager


class AbstractOutputWriter(ABC):
    def __init__(self):
        self._indent = 0

    @abstractmethod
    def write(self, message):
        pass

    def increase_indent(self):
        self._indent += 2

    def decrease_indent(self):
        self._indent -= 2

    @contextmanager
    def indent(self):
        self.increase_indent()
        yield
        self.decrease_indent()


class OutputWriter(AbstractOutputWriter):
    def __init__(self):
        super().__init__()

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(logging.Formatter('%(message)s'))

        logger = logging.Logger('darty.output')
        logger.addHandler(stream_handler)

        self._logger = logger

    def write(self, message: str):
        self._logger.info(' ' * self._indent + message)


class NullOutputWriter(AbstractOutputWriter):
    def __init__(self):
        super().__init__()

    def write(self, message):
        pass
