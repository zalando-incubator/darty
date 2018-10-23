from abc import ABC, abstractmethod
from darty.output_writer import AbstractOutputWriter


class AbstractDriver(ABC):
    """
    This class enables to abstract the storage layer responsible for centrally storing packages and their versions.
    Drivers for new storage mediums can be added by inheriting this class. Any capability used for the storage layer
    should be configured to guarantee immutability in order for the darty to work properly
    """
    def __init__(self, root: str, parameters: dict = None):
        self._root = root
        self._params = parameters if parameters else {}

    @abstractmethod
    def download_package(self, group: str, artifact: str, version: str,
                         tmp_artifact_dir: str, output: AbstractOutputWriter):
        """Downloads the package from a repository to the temporary directory."""
        pass

    @abstractmethod
    def upload_package(self, group: str, artifact: str, version: str,
                       tmp_artifact_dir: str, output: AbstractOutputWriter):
        """Uploads the package from the temporary directory to a repository."""
        pass


class DriverError(Exception):
    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self):
        return self.msg


class PackageNotFoundError(DriverError):
    def __init__(self, msg: str = 'Package not found'):
        super().__init__(msg)


class VersionExistsError(DriverError):
    def __init__(self, msg: str = 'This version of the package already exists in the repository'):
        super().__init__(msg)


class ReadAccessError(DriverError):
    def __init__(self, msg: str = 'No read access'):
        super().__init__(msg)


class WriteAccessError(DriverError):
    def __init__(self, msg: str = 'No write access'):
        super().__init__(msg)
