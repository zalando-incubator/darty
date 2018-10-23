import os
from darty.drivers.abstract import AbstractDriver
from darty.output_writer import AbstractOutputWriter
from darty.utils import file_exists, copy_dir


class TestDriver(AbstractDriver):
    """Driver class for unit tests."""
    def __init__(self, root: str, parameters: dict):
        super().__init__(root, parameters)

        assert 'local_dir' in parameters

        # create a directory for the repository
        os.makedirs(parameters['local_dir'], exist_ok=True)

        self._repository_dir = parameters['local_dir']
        self._bucket_name = root

    def download_package(self, group: str, artifact: str, version: str,
                         tmp_artifact_dir: str, output: AbstractOutputWriter) -> bool:
        artifact_dir = self._get_artifact_dir(group, artifact, version)

        # download a file
        copy_dir(artifact_dir, tmp_artifact_dir)

        return True

    def upload_package(self, group: str, artifact: str, version: str,
                       tmp_artifact_dir: str, output: AbstractOutputWriter) -> bool:
        artifact_dir = self._get_artifact_dir(group, artifact, version)

        # upload a file
        os.makedirs(os.path.dirname(artifact_dir), exist_ok=True)
        copy_dir(tmp_artifact_dir, artifact_dir)

        return True

    def package_exists(self, group: str, artifact: str, version: str) -> bool:
        artifact_path = self._get_artifact_dir(group, artifact, version)
        return file_exists(artifact_path)

    def _get_artifact_dir(self, group: str, artifact: str, version: str):
        """Path to local artifact directory."""
        artifact_dir = os.path.join(self._repository_dir, self._bucket_name, group.replace('.', os.sep),
                                    artifact + '-' + version)
        return artifact_dir
