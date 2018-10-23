import unittest
import os
import boto3
from darty.drivers.abstract import VersionExistsError, PackageNotFoundError
from darty.drivers.s3.files.driver import S3FilesDriver
from darty.drivers.s3.zip.driver import S3ZipDriver
from moto import mock_s3
from darty.output_writer import NullOutputWriter
from shutil import rmtree


def list_dir_files(dir_path):
    for cur_dir, directories, filenames in os.walk(dir_path):
        rel_dir = os.path.relpath(cur_dir, dir_path)
        for filename in filenames:
            yield os.path.join(rel_dir, filename)


class TestDrivers(unittest.TestCase):
    @mock_s3
    def test_upload_and_download(self):
        for driver_class in [S3FilesDriver, S3ZipDriver]:
            # create a test bucket
            bucket_name = 'test-bucket-%s' % driver_class.__name__
            s3 = boto3.resource('s3')
            s3.create_bucket(Bucket=bucket_name)

            driver = driver_class(bucket_name, {})

            # upload test package
            pkg1_path = os.path.join(os.path.dirname(__file__), 'data', 'packages', 'package1')
            driver.upload_package('group1', 'artifact1', '1.1', pkg1_path, output=NullOutputWriter())

            # upload the same package second time (raises an exception)
            with self.assertRaises(VersionExistsError):
                driver.upload_package('group1', 'artifact1', '1.1', pkg1_path, output=NullOutputWriter())

            # create a folder for downloaded package
            downloaded_pkg_path = os.path.join(os.path.dirname(__file__), 'data', 'packages', 'downloaded')
            rmtree(downloaded_pkg_path, ignore_errors=True)
            os.makedirs(downloaded_pkg_path, exist_ok=True)

            # download the package
            driver.download_package('group1', 'artifact1', '1.1', downloaded_pkg_path, output=NullOutputWriter())
            orig_files = list(list_dir_files(pkg1_path))
            downloaded_files = list(list_dir_files(downloaded_pkg_path))
            self.assertEqual(orig_files, downloaded_files)
            rmtree(downloaded_pkg_path, ignore_errors=True)

            # download not-existing package (raises an exception)
            with self.assertRaises(PackageNotFoundError):
                driver.download_package('group1', 'artifact_doesnt_exist', '1.0', downloaded_pkg_path,
                                        output=NullOutputWriter())


if __name__ == '__main__':
    unittest.main()
