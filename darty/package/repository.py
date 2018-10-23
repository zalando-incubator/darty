from darty.drivers.factory import DriverFactory
from darty.package.validators import check_repository_root, check_repository_type


class Repository(object):

    def __init__(self, config: dict):
        self.type = config.get('type', '')
        self.root = config.get('root', '')  # unique identificator within particular repository type
        self.parameters = config.get('parameters', {})

        # check repository type
        if not self.type:
            raise ValueError('Repository type must be specified')
        if not check_repository_type(self.type):
            raise ValueError('Repository type has invalid format')

        # check repository root
        if not self.root:
            raise ValueError('Repository root must be specified')
        if not check_repository_root(self.root):
            raise ValueError('Repository root has invalid format')

        self._driver = None

    @property
    def driver(self):
        if not self._driver:
            self._driver = DriverFactory.create_driver(self.type, self.root, self.parameters)

        return self._driver
