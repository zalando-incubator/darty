import os
import boto3
from darty.drivers.abstract import AbstractDriver, VersionExistsError, DriverError, PackageNotFoundError, \
    ReadAccessError
from darty.output_writer import AbstractOutputWriter
from darty.drivers.s3.zip.utils import pack_archive, unpack_archive
from botocore.exceptions import ClientError


class S3ZipDriver(AbstractDriver):

    def __init__(self, root: str, parameters: dict):
        super().__init__(root, parameters)

        self._s3 = boto3.resource('s3')
        self._client = self._s3.meta.client

    def download_package(self, group: str, artifact: str, version: str,
                         tmp_artifact_dir: str, output: AbstractOutputWriter):
        # check that package exists in the repository
        package_exists = self._package_exists(group, artifact, version)
        if not package_exists:
            raise PackageNotFoundError()

        # download an archive
        s3_path = self._get_s3_artifact_path(group, artifact, version)
        archive_path = os.path.join(tmp_artifact_dir, 'package.zip')

        try:
            self._s3.Bucket(self._root).download_file(s3_path, archive_path)
        except ClientError as e:
            raise DriverError('Download Error: %s' % e.response['Error']['Message'])

        # unarchive a package
        unpack_archive(archive_path, tmp_artifact_dir)

        # remove an archive
        os.remove(archive_path)

    def upload_package(self, group: str, artifact: str, version: str,
                       tmp_artifact_dir: str, output: AbstractOutputWriter):
        # check that this version of the package doesn't exist in the repository
        package_exists = self._package_exists(group, artifact, version)
        if package_exists:
            raise VersionExistsError()

        # archive a package
        archive_path = os.path.join(tmp_artifact_dir, 'package.zip')
        pack_archive(tmp_artifact_dir, archive_path)

        # upload an archive to S3
        s3_path = self._get_s3_artifact_path(group, artifact, version)
        try:
            self._client.upload_file(archive_path, self._root, s3_path)
        except ClientError as e:
            raise DriverError('Upload Error: %s' % e.response['Error']['Message'])

        # remove an archive
        os.remove(archive_path)

    def _package_exists(self, group: str, artifact: str, version: str) -> bool:
        path = self._get_s3_artifact_path(group, artifact, version)
        exists = True

        try:
            self._client.head_object(Bucket=self._root, Key=path)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                exists = False
            elif e.response['Error']['Code'] == '403':
                raise ReadAccessError()
            else:
                raise DriverError(e.response['Error']['Message'])

        return exists

    @staticmethod
    def _get_s3_artifact_path(group: str, artifact: str, version: str):
        path = group.replace('.', '/') + '/' + artifact + '-' + version + '.zip'
        return path
