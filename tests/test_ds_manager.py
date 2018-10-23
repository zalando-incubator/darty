import unittest
import os
from darty.dependency_manager import DependencyManager
from schema import SchemaError


def get_config_path(config_filename: str):
    return os.path.join(os.path.dirname(__file__), 'data', 'configs', config_filename)


class TestDependencyManager(unittest.TestCase):

    def test_configuration(self):
        # configuration file doesn't exist
        with self.assertRaises(ValueError):
            DependencyManager('file_doesnt_exist.yaml')

        # no repositories specified
        with self.assertRaises(SchemaError):
            DependencyManager(get_config_path('without_repositories.yaml'))

        # no dependencies specified
        with self.assertRaises(ValueError):
            DependencyManager(get_config_path('without_dependencies.yaml'))

        # broken dependency specified
        with self.assertRaises(SchemaError):
            DependencyManager(get_config_path('broken_dependency.yaml'))

        # repository with such name not found in the configuration file
        with self.assertRaises(ValueError):
            DependencyManager(get_config_path('repository_not_found.yaml'))

        # broken repository specified
        with self.assertRaises(ValueError):
            DependencyManager(get_config_path('broken_repository.yaml'))

        # different versions of the same package are specified
        with self.assertRaises(ValueError):
            DependencyManager(get_config_path('duplicated_dependency.yaml'))

    def test_get_dependency(self):
        dm = DependencyManager(get_config_path('darty.yaml'))

        # get dependency by name
        dependency = dm.get_dependency_by_name('group1', 'artifact1')
        self.assertEqual(dependency.group, 'group1')
        self.assertEqual(dependency.artifact, 'artifact1')

        self.assertIsNone(dm.get_dependency_by_name('group1', 'wrong-artifact'))


if __name__ == '__main__':
    unittest.main()
