class PackageInfo(object):

    def __init__(self, config: dict, local: bool):
        """
        :param config: package configuration (from "info.json" file)
        :param local: True if this package published locally, False otherwise
        """
        # TODO: check for errors
        self.group = config['group']
        self.artifact = config['artifact']
        self.version = config['version']
        self.files = config['files']
        self.name = config.get('name', '')
        self.description = config.get('description', '')

        self.local = local
