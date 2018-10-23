from argparse import Namespace, ArgumentParser
from darty.commands.abstract import AbstractCommand
from darty.dependency_manager import DependencyManager
from darty.helpers.commands import get_dependencies_by_name
from darty.output_writer import AbstractOutputWriter


class DownloadCommand(AbstractCommand):

    @staticmethod
    def get_command_name():
        return 'download'

    @staticmethod
    def get_description():
        return 'Download dependencies'

    def configure(self, subparser: ArgumentParser):
        subparser.add_argument('-c', '--config', type=str, help='Path to the model\'s config file', default=None)
        subparser.add_argument('--py-package', type=str, help='Python package that contains Darty configuration file',
                               default=None)
        subparser.add_argument('--group', type=str, help='Group name of the package to download', default=None)
        subparser.add_argument('--artifact', type=str, help='Artifact name of the package to download', default=None)

    def run(self, args: Namespace, settings: dict, output: AbstractOutputWriter):
        # instantiate the manager
        if args.py_package:
            try:
                manager = DependencyManager.from_py_package(args.py_package, args.profile)
            except ImportError:
                raise ValueError('Python package "%s" not found' % args.py_package)
        else:
            manager = DependencyManager(args.config, args.profile)

        # get dependencies
        dependencies = get_dependencies_by_name(manager, args.group, args.artifact)

        if not dependencies:
            output.write('No dependencies found')
        else:
            # download dependencies
            for dependency in dependencies:
                dependency.download(output)
                output.write('')
