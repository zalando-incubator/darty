import re
import os
from setuptools import setup, find_packages


def get_version():
    version_re = re.compile(r'''__version__ = ['"]([0-9.]+)['"]''')
    init = open(os.path.join(os.path.dirname(__file__), 'darty', '__init__.py')).read()
    return version_re.search(init).group(1)


setup(
    name='darty',
    version=get_version(),
    description='Data Dependency Manager',
    packages=find_packages(exclude=['tests*']),
    scripts=['bin/darty'],
    entry_points={
        'darty_drivers': [
            'test = darty.drivers.test.driver:TestDriver',
            's3_files = darty.drivers.s3.files.driver:S3FilesDriver',
            's3_zip = darty.drivers.s3.zip.driver:S3ZipDriver',
        ],
    },
    install_requires=['boto3', 'schema'],
    tests_require=['moto'],
    test_suite='tests',
)
