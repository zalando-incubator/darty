import configparser
import os
from darty.utils import check_path


def get_config_file_path():
    """Path to Darty "config" file."""
    return os.path.join(os.path.expanduser('~'), '.darty', 'config')


def get_settings(profile: str = 'default'):
    """Returns Darty settings for a specific profile."""
    return get_profile_settings(get_config_file_path(), profile, {
        'packages_dir': os.path.join(os.path.dirname(get_config_file_path()), 'packages')
    })


def get_profile_settings(filename: str, section: str, defaults: dict):
    """Reads a particular section in a configuration file.
    Args:
        filename (str): Path to a configuration file.
        section (str): Section name which should be read.
        defaults (dict): Dictionary with default values.
    Returns:
        dict: Default values merged with the actual values from the section.
    """
    config = configparser.ConfigParser()
    config.read(filename)

    settings = dict(defaults)
    if section in config:
        settings = {**settings, **config[section]}

    return settings


def save_profile_settings(filename: str, section: str, settings: dict):
    """Saves a particular section to a configuration file.
    Args:
        filename (str): Path to a configuration file.
        section (str): Section name where to write the settings.
        settings (dict): Dictionary with settings to save.
    """
    config = configparser.ConfigParser()
    config.read(filename)
    config[section] = settings

    check_path(os.path.dirname(filename))

    with open(filename, 'w') as f:
        config.write(f)
