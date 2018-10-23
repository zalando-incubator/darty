from argparse import Namespace
from darty.commands.abstract import AbstractCommand
from darty.output_writer import AbstractOutputWriter
from darty.settings import save_profile_settings, get_config_file_path
from darty.utils import get_input


class ConfigureCommand(AbstractCommand):

    @staticmethod
    def get_command_name():
        return 'configure'

    @staticmethod
    def get_description():
        return 'Configure the tool'

    def run(self, args: Namespace, settings: dict, output: AbstractOutputWriter):
        # ask the user to update Darty config
        inputs = [
            ('packages_dir', 'Directory where all the packages will be stored [%s]: '),
            # TODO: include settings necessary for drivers
        ]

        for setting, message in inputs:
            settings[setting] = get_input(message % str(settings[setting]), settings[setting])

        # save the config file
        save_profile_settings(get_config_file_path(), args.profile, settings)

        return True
