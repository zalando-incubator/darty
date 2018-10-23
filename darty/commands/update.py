from argparse import Namespace, ArgumentParser
from darty.commands.abstract import AbstractCommand
from darty.dependency_manager import DependencyManager
from darty.helpers.commands import get_dependencies_by_name
from darty.output_writer import AbstractOutputWriter


class UpdateCommand(AbstractCommand):

    @staticmethod
    def get_command_name():
        return 'update'

    @staticmethod
    def get_description():
        return 'Update dependencies'

    def configure(self, subparser: ArgumentParser):
        subparser.add_argument('-c', '--config', type=str, help='Path to the model\'s config file', default=None)
        subparser.add_argument('--group', type=str, help='Group name of the package to update', default=None)
        subparser.add_argument('--artifact', type=str, help='Artifact name of the package to update', default=None)
        subparser.add_argument('-r', '--rewrite', action='store_true', help='Rewrite working directories')

    def run(self, args: Namespace, settings: dict, output: AbstractOutputWriter):
        # instantiate the manager
        manager = DependencyManager(args.config, args.profile)

        # get dependencies
        dependencies = get_dependencies_by_name(manager, args.group, args.artifact)

        if not dependencies:
            output.write('No dependencies found')
        else:
            # update dependencies
            for dependency in dependencies:
                dependency.update(args.rewrite, output)
                output.write('')
