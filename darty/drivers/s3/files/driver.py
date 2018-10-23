import logging
import os
import boto3
from botocore.exceptions import ClientError
from darty.drivers.abstract import AbstractDriver, PackageNotFoundError, ReadAccessError, DriverError, \
    VersionExistsError
from darty.output_writer import AbstractOutputWriter
from darty.drivers.s3.files.utils import get_dir_files


class S3FilesDriver(AbstractDriver):

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

        # get a list of package files
        s3_prefix = self._get_s3_file_path(group, artifact, version, '')

        bucket = self._s3.Bucket(self._root)
        try:
            s3_file_paths = [obj.key for obj in bucket.objects.filter(Prefix=s3_prefix)]
        except ClientError as e:
            raise DriverError(e.response['Error']['Message'])

        # download the files
        bucket = self._s3.Bucket(self._root)
        for s3_file_path in s3_file_paths:
            local_file_path = os.path.join(tmp_artifact_dir, s3_file_path[len(s3_prefix):])

            logging.debug('Downloading "s3://%s/%s" to "%s"' % (self._root, s3_file_path, local_file_path))

            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            try:
                bucket.download_file(s3_file_path, local_file_path)
            except ClientError as e:
                if e.response['Error']['Code'] == '403':
                    raise ReadAccessError()
                else:
                    raise DriverError('Download Error: %s' % e.response['Error']['Message'])

    def upload_package(self, group: str, artifact: str, version: str,
                       tmp_artifact_dir: str, output: AbstractOutputWriter):
        # check that this version of the package doesn't exist in the repository
        package_exists = self._package_exists(group, artifact, version)
        if package_exists:
            raise VersionExistsError()

        # upload files to S3
        for file_path in get_dir_files(tmp_artifact_dir):
            s3_file_path = self._get_s3_file_path(group, artifact, version, file_path)
            local_file_path = os.path.join(tmp_artifact_dir, file_path)

            logging.debug('Uploading "%s" to "s3://%s/%s"' % (local_file_path, self._root, s3_file_path))

            try:
                self._client.upload_file(os.path.join(tmp_artifact_dir, file_path), self._root, s3_file_path)
            except ClientError as e:
                raise DriverError('Upload Error: %s' % e.response['Error']['Message'])

    def _package_exists(self, group: str, artifact: str, version: str) -> bool:
        prefix = self._get_s3_file_path(group, artifact, version, '')

        try:
            res = self._client.list_objects_v2(Bucket=self._root, Prefix=prefix)
        except ClientError as e:
            if e.response['Error']['Code'] == '403':
                raise ReadAccessError()
            else:
                raise DriverError(e.response['Error']['Message'])

        return bool(res['KeyCount'])

    @staticmethod
    def _get_s3_file_path(group: str, artifact: str, version: str, file_path: str) -> str:
        path = group.replace('.', '/') + '/.artifacts/' + artifact + '-' + version + '/' + file_path
        return path
