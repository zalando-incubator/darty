import yaml
import os
from collections import OrderedDict

from darty.helpers.validation import validate_dependency_config
from darty.package.dependency import Dependency
from darty.package.repository import Repository
from darty.settings import get_settings
from darty.utils import file_exists


class DependencyManager(object):
    """This class reads, maintains and indexes all the known dependencies in the project."""

    DEFAULT_CONFIG_FILE = 'darty.yaml'
    DEFAULT_DARTY_PROFILE = 'default'

    def __init__(self, config_path: str = None, darty_profile: str = None):
        if not config_path:
            config_path = self.DEFAULT_CONFIG_FILE

        if not darty_profile:
            darty_profile = self.DEFAULT_DARTY_PROFILE

        # check that a configuration file exists
        if not file_exists(config_path):
            raise ValueError('Configuration file "%s" was not found.' % config_path)

        # get packages directory
        settings = get_settings(darty_profile)
        packages_dir = os.path.expanduser(settings['packages_dir'])

        # read a config file
        with open(config_path, 'r') as f:
            config = yaml.load(f)

        config = validate_dependency_config(config)

        project_dir = os.path.dirname(config_path)  # project directory

        if 'repositories' not in config or not len(config['repositories']):
            raise ValueError('Repositories are not specified')

        if 'dependencies' not in config or not len(config['dependencies']):
            raise ValueError('Dependencies are not specified')

        # creating repositories objects
        repositories = {}
        for rep_name, rep_config in config['repositories'].items():
            try:
                repositories[rep_name] = Repository(rep_config)
            except ValueError as e:
                raise ValueError('Repository "%s": %s' % (rep_name, str(e)))

        # creating dependency objects
        self._dependencies = OrderedDict()

        for i, dep_config in enumerate(config['dependencies']):
            # get repository object
            repository_name = dep_config['repository'] if 'repository' in dep_config else 'default'
            if repository_name not in repositories:
                raise ValueError('Repository "%s" doesn\'t exist' % repository_name)

            # create an object for dependency
            try:
                dependency = Dependency(dep_config, repositories[repository_name], packages_dir, project_dir)
            except ValueError as e:
                raise ValueError('Dependency #%d: %s' % (i + 1, str(e)))

            key = self._get_dependency_key(dependency.group, dependency.artifact)

            if key in self._dependencies:
                raise ValueError('Config contains two dependencies with the same name: "%s:%s"'
                                 % (dependency.group, dependency.artifact))

            self._dependencies[key] = dependency

        # TODO:
        # check that dependencies with the same working directories
        # always contain "files" parameter and files are not overlapped

    @property
    def dependencies(self):
        return self._dependencies

    @classmethod
    def from_py_package(cls, package_name: str, config_path: str = None, darty_profile: str = None):
        """Creates an instance of DependencyManager by Python package name.
        It automatically finds a path to dependency file within a Python package.

        :param package_name:
        :param config_path:
        :param darty_profile:
        :return:
        """
        import pkg_resources

        if not config_path:
            config_path = cls.DEFAULT_CONFIG_FILE

        return cls(pkg_resources.resource_filename(package_name, config_path), darty_profile)

    def get_path(self, group: str, artifact: str, file_path: str = None):
        dependency = self.get_dependency_by_name(group, artifact)
        if not dependency:
            raise ValueError('The package "%s:%s" was not found in the configuration file' % (group, artifact))

        return dependency.get_path(file_path)

    def get_dependency_by_name(self, group: str, artifact: str) -> Dependency:
        """Returns dependency object by group and artifact name or "None" if the dependency is not specified.

        :param group:
        :param artifact:
        :return: Dependency
        """
        name = self._get_dependency_key(group, artifact)
        if name not in self._dependencies:
            return None

        return self._dependencies[name]

    def search_dependency_by_artifact(self, artifact: str) -> list:
        """Finds dependencies by artifact name.

        :param artifact:
        :return: [Dependency]
        """
        res = []
        for key, dependency in self._dependencies.items():
            if dependency.artifact == artifact:
                res.append(dependency)

        return res

    def _get_dependency_key(self, group, artifact):
        """Returns a unique key for dependency for faster lookups."""
        return group + '.' + artifact
