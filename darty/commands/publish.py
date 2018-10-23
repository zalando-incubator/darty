from argparse import Namespace, ArgumentParser
from darty.commands.abstract import AbstractCommand
from darty.dependency_manager import DependencyManager
from darty.helpers.commands import get_dependencies_by_name
from darty.output_writer import AbstractOutputWriter


class PublishCommand(AbstractCommand):

    @staticmethod
    def get_command_name():
        return 'publish'

    @staticmethod
    def get_description():
        return 'Publish package'

    def configure(self, subparser: ArgumentParser):
        subparser.add_argument('-c', '--config', type=str, help='Path to the model\'s config file', default=None)
        subparser.add_argument('--group', type=str, help='Group name of the package to publish', default=None)
        subparser.add_argument('--artifact', type=str, help='Artifact name of the package to publish', default=None)

    def run(self, args: Namespace, settings: dict, output: AbstractOutputWriter):
        # get the dependency to publish
        dependency = self._resolve_dependency(args, output)

        # publish the package
        dependency.publish(output=output)

    @staticmethod
    def _resolve_dependency(args: Namespace, output: AbstractOutputWriter):
        # instantiate the manager
        manager = DependencyManager(args.config, args.profile)

        # get dependencies
        dependencies = get_dependencies_by_name(manager, args.group, args.artifact)
        if not dependencies:
            raise ValueError('No packages to publish')

        if len(dependencies) > 1:
            # ask user to choose a package to publish
            output.write('Multiple packages detected, select one to publish:\n')
            with output.indent():
                for i, dependency in enumerate(dependencies):
                    output.write('[%d] %s:%s:%s' % (i + 1, dependency.group, dependency.artifact, dependency.version))

            output.write('')

            try:
                num = int(input('Enter number: '))
            except ValueError:
                raise ValueError('\nWrong value.')

            if num > len(dependencies):
                raise ValueError('Value between 1 and %d was expected.' % num)
        else:
            num = 1

        return dependencies[num - 1]
