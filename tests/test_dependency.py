import unittest
import os
from darty.package.dependency import Dependency
from darty.package.repository import Repository
from darty.utils import file_exists, dir_exists, list_dir_files
from shutil import rmtree


class TestDependency(unittest.TestCase):

    PROJECT_DIR = os.path.join(os.path.dirname(__file__), 'data', 'test_project_dir')
    PACKAGES_DIR = os.path.join(os.path.dirname(__file__), 'data', 'test_packages_dir')

    REPOSITORY_TYPE = 'test'
    REPOSITORY_ROOT = 'test_root'
    REPOSITORY_DIR = os.path.join(os.path.dirname(__file__), 'data', 'test_repository')

    @classmethod
    def _get_dependency(cls, config: dict):
        return Dependency(config, Repository({
            'type': cls.REPOSITORY_TYPE,
            'root': cls.REPOSITORY_ROOT,
            'parameters': {
                'local_dir': cls.REPOSITORY_DIR
            }
        }), cls.PACKAGES_DIR, cls.PROJECT_DIR)

    def test_get_path(self):
        dep_installed = self._get_dependency({
            'group': 'group1.subgroup1',
            'artifact': 'artifact1',
            'version': '1.0',
        })

        dep_not_installed = self._get_dependency({
            'group': 'group1.subgroup1',
            'artifact': 'artifact1-not-installed',
            'version': '1.0',
        })

        dep_working_dir_exists = self._get_dependency({
            'group': 'group1.subgroup1',
            'artifact': 'artifact1',
            'version': '1.0',
            'workingDir': 'working_dir1',
        })

        dep_working_dir_doesnt_exist = self._get_dependency({
            'group': 'group1.subgroup1',
            'artifact': 'artifact1',
            'version': '1.0',
            'workingDir': 'working_dir_doesnt_exist',
        })

        dep_files = self._get_dependency({
            'group': 'group1.subgroup1',
            'artifact': 'artifact1',
            'version': '1.0',
            'workingDir': 'working_dir1',
            'files': [
                'file1.txt',
                'file2.txt',
                'subdir1/file1.txt',
            ]
        })

        dep_repository_dir = os.path.join(self.PACKAGES_DIR, self.REPOSITORY_TYPE, self.REPOSITORY_ROOT)
        dependency_data_dir = os.path.join(dep_repository_dir, 'group1', 'subgroup1', '.artifacts', 'artifact1-1.0', 'data')
        working_dir = os.path.join(self.PROJECT_DIR, 'working_dir1')

        """ TEST PATHS TO A PACKAGE DIRECTORY """

        # package is not installed
        with self.assertRaises(ValueError):
            dep_not_installed.get_path()

        # package without working directory
        path = dep_installed.get_path()
        self.assertEqual(path, dependency_data_dir)

        """ A WORKING DIRECTORY IS SPECIFIED IN THE DEPENDENCY CONFIGURATION """

        # the working directory exists
        path = dep_working_dir_exists.get_path()
        self.assertEqual(path, working_dir)

        # the working directory doesn't exists
        path = dep_working_dir_doesnt_exist.get_path()
        self.assertEqual(path, dependency_data_dir)

        """ TEST PATHS TO A PACKAGE FILE """

        # package is not installed
        with self.assertRaises(ValueError):
            dep_not_installed.get_path('file1.txt')

        # package without working directory
        path = dep_installed.get_path('subdir1/file1.txt')
        self.assertEqual(path, os.path.join(dependency_data_dir, 'subdir1', 'file1.txt'))

        """ A WORKING DIRECTORY IS SPECIFIED IN THE DEPENDENCY CONFIGURATION """

        # package with working directory, the file exists
        path = dep_working_dir_exists.get_path('subdir1/file1.txt')
        self.assertEqual(path, os.path.join(working_dir, 'subdir1', 'file1.txt'))

        # the file exists (windows format path)
        path = dep_working_dir_exists.get_path('subdir1\\file1.txt')
        self.assertEqual(path, os.path.join(working_dir, 'subdir1', 'file1.txt'))

        # the file doesn't exists in the working directory
        path = dep_working_dir_exists.get_path('file2.txt')
        self.assertEqual(path, os.path.join(dependency_data_dir, 'file2.txt'))

        # the working directory doesn't exists
        path = dep_working_dir_doesnt_exist.get_path('subdir1/file1.txt')
        self.assertEqual(path, os.path.join(dependency_data_dir, 'subdir1', 'file1.txt'))

        # the file doesn't exists in the package
        with self.assertRaises(FileNotFoundError):
            dep_working_dir_exists.get_path('file_doesnt_exist.txt')

        """ A FILES LIST IS SPECIFIED IN THE DEPENDENCY CONFIGURATION """

        # the file is in the list, the file exists in the working directory
        path = dep_files.get_path('subdir1/file1.txt')
        self.assertEqual(path, os.path.join(working_dir, 'subdir1', 'file1.txt'))

        # the file doesn't exists in the working directory
        path = dep_files.get_path('file2.txt')
        self.assertEqual(path, os.path.join(dependency_data_dir, 'file2.txt'))

        # package with files, the file is not in the list
        with self.assertRaises(ValueError):
            dep_files.get_path('file_not_in_list.txt')

    def test_publish_and_update(self):
        dep_without_working_dir = self._get_dependency({
            'group': 'group1.subgroup1',
            'artifact': 'artifact1',
            'version': '1.1',
        })

        dep_to_publish = self._get_dependency({
            'group': 'group1.subgroup1',
            'artifact': 'artifact1',
            'version': '1.1',
            'workingDir': 'working_dir1',
        })

        dep_to_update = self._get_dependency({
            'group': 'group1.subgroup1',
            'artifact': 'artifact1',
            'version': '1.1',
            'workingDir': 'working_dir_update',
        })

        # dependency paths
        group_dir = os.path.join(self.PACKAGES_DIR, self.REPOSITORY_TYPE, self.REPOSITORY_ROOT, 'group1', 'subgroup1')

        installation_dir = os.path.join(group_dir, '.artifacts', 'artifact1-1.1')
        installation_data_dir = os.path.join(installation_dir, 'data')
        local_installation_dir = os.path.join(group_dir, '.local-artifacts', 'artifact1-1.1')
        local_installation_data_dir = os.path.join(local_installation_dir, 'data')

        working_dir = os.path.join(self.PROJECT_DIR, 'working_dir1')
        working_dir_update = os.path.join(self.PROJECT_DIR, 'working_dir_update')

        # path to local repository (using TestDriver)
        rep_root_dir = os.path.join(self.REPOSITORY_DIR, self.REPOSITORY_ROOT)
        rep_artifact_dir = os.path.join(rep_root_dir, 'group1', 'subgroup1', 'artifact1-1.1')

        """ PREPARE THE TEST """

        # clear installed package
        if dir_exists(installation_dir):
            rmtree(installation_dir)

        # clear locally installed package
        if dir_exists(local_installation_dir):
            rmtree(local_installation_dir)

        # clear package in the repository
        if dir_exists(rep_root_dir):
            rmtree(rep_root_dir)

        # clear "update" working directory
        if dir_exists(working_dir_update):
            rmtree(working_dir_update)

        # check that the right paths are returned
        self.assertEqual(dep_to_publish.get_path(), working_dir)

        with self.assertRaises(ValueError):
            dep_without_working_dir.get_path()

        with self.assertRaises(ValueError):
            dep_to_update.get_path()

        """ PUBLISHING LOCALLY """

        # publish repository locally
        dep_to_publish.publish(local=True)
        self.assertEqual(dep_without_working_dir.get_path(), local_installation_data_dir)

        # should return False because the package already published locally
        res = dep_to_publish.publish(local=True)
        self.assertFalse(res)

        # rewrite locally published package
        dep_to_publish.publish(local=True, rewrite_local=True)
        self.assertEqual(dep_without_working_dir.get_path(), local_installation_data_dir)

        # remove locally installed package
        rmtree(local_installation_dir)
        with self.assertRaises(ValueError):
            dep_without_working_dir.get_path()

        """ PUBLISHING TO THE TEST REPOSITORY """

        # publish repository
        dep_to_publish.publish()

        files_to_check = [
            'info.json',
            os.path.join('data', 'file1.txt'),
            os.path.join('data', 'subdir1', 'file1.txt'),
        ]
        for file_path in files_to_check:
            self.assertTrue(file_exists(os.path.join(rep_artifact_dir, file_path)),
                            'File "%s" doesn\'t exist in the repository' % file_path)

        self.assertEqual(dep_without_working_dir.get_path(), installation_data_dir)

        # should return False because the package already exists in the repository
        res = dep_to_publish.publish()
        self.assertFalse(res)

        # check that the right paths are returned
        self.assertEqual(dep_to_publish.get_path(), working_dir)
        self.assertEqual(dep_to_update.get_path(), installation_data_dir)

        # remove the installed package
        rmtree(installation_dir)
        with self.assertRaises(ValueError):
            dep_to_update.get_path()

        """ DOWNLOAD THE PACKAGE """

        # download the package
        dep_to_update.download()
        self.assertEqual(dep_to_update.get_path(), installation_data_dir)

        # remove the installed package again
        rmtree(installation_dir)
        with self.assertRaises(ValueError):
            dep_to_update.get_path()

        """ UPDATE THE DEPENDENCY """

        # update the dependency (working directory should be created)
        dep_to_update.update()
        self.assertEqual(dep_to_update.get_path(), working_dir_update)

        # remove the package after test
        rmtree(installation_dir)
        rmtree(rep_root_dir)
        rmtree(working_dir_update)

    def test_publish_files(self):
        dep_without_working_dir = self._get_dependency({
            'group': 'group1.subgroup1',
            'artifact': 'artifact1',
            'version': '1.1',
        })

        dep_to_publish = self._get_dependency({
            'group': 'group1.subgroup1',
            'artifact': 'artifact1',
            'version': '1.1',
            'workingDir': 'working_dir1',
            'files': [
                'subdir1/file1.txt',
            ]
        })

        dep_file_doesnt_exist = self._get_dependency({
            'group': 'group1.subgroup1',
            'artifact': 'artifact1',
            'version': '1.1',
            'workingDir': 'working_dir1',
            'files': [
                'file_doesnt_exist.txt',
            ]
        })

        group_dir = os.path.join(self.PACKAGES_DIR, self.REPOSITORY_TYPE, self.REPOSITORY_ROOT, 'group1', 'subgroup1')
        local_installation_dir = os.path.join(group_dir, '.local-artifacts', 'artifact1-1.1')

        # clear locally installed package
        if dir_exists(local_installation_dir):
            rmtree(local_installation_dir)

        # publishing file doesn't exist in the working directory
        res = dep_file_doesnt_exist.publish(local=True)
        self.assertFalse(res)

        # publish package locally
        dep_to_publish.publish(local=True)

        # TODO: fix paths logic and tests for Windows
        published_files = list(list_dir_files(dep_without_working_dir.get_path()))
        self.assertEqual(published_files, dep_to_publish.files)

        # remove the package after test
        rmtree(local_installation_dir)


if __name__ == '__main__':
    unittest.main()
