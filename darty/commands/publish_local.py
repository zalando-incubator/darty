from argparse import Namespace, ArgumentParser
from darty.commands.publish import PublishCommand
from darty.output_writer import AbstractOutputWriter


class PublishLocalCommand(PublishCommand):

    @staticmethod
    def get_command_name():
        return 'publish-local'

    @staticmethod
    def get_description():
        return 'Publish package locally'

    def configure(self, subparser: ArgumentParser):
        super().configure(subparser)
        subparser.add_argument('-r', '--rewrite', action='store_true',
                               help='Rewrite local package if it exists')

    def run(self, args: Namespace, settings: dict, output: AbstractOutputWriter):
        # get the dependency to publish
        dependency = self._resolve_dependency(args, output)

        # publish the package
        dependency.publish(local=True, rewrite_local=args.rewrite, output=output)
