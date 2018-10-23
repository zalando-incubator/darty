import pkg_resources
from darty.drivers.abstract import AbstractDriver
from darty.drivers.test.driver import TestDriver


class DriverFactory(object):
    @classmethod
    def create_driver(cls, driver_name, root: str, parameters: dict) -> AbstractDriver:
        # driver for unit tests
        if driver_name == 'test':
            return TestDriver(root, parameters)

        # search the driver
        for entry_point in pkg_resources.iter_entry_points('darty_drivers'):
            if driver_name == entry_point.name:
                driver = entry_point.load()
                return driver(root, parameters)

        raise ValueError('Driver "%s" not found' % driver_name)
