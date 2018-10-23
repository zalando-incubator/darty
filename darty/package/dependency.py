import json
import os
from collections import OrderedDict
from shutil import rmtree
from darty.output_writer import AbstractOutputWriter, NullOutputWriter
from darty.package.package_info import PackageInfo
from darty.package.repository import Repository
from darty.package.validators import check_group_name, check_artifact_name, check_version_number, \
     check_files_file_path
from darty.utils import file_exists, dir_exists, get_dir_hash, is_dir_empty, copy_dir, copy_file


class Dependency(object):
    """
    Key class describing a dependency and enabling to resolve a paths to the files containing the dependency's content
    On the current machine, a dependency is stored under:
    ${local_cache}/${repository_type}/${repository_root}/${group_name}/${development_stage}/$(${artifact_name}+'-'+${version})
    during update
    """

    ENV_PRODUCTION = '.artifacts'
    ENV_LOCAL = '.local-artifacts'
    ENV_TMP = '.tmp-artifacts'

    def __init__(self, config: dict, repository: Repository, packages_dir: str, project_dir: str):

        self.group = config.get('group', '')
        self.artifact = config.get('artifact', '')
        self.version = config.get('version', '')
        self.working_dir = config.get('working-dir', None)
        self.files = config.get('files', None)
        self.default_file = config.get('default-file', None)
        self.name = config.get('name', '')
        self.description = config.get('description', '')

        self.repository = repository
        self.packages_dir = packages_dir
        self.project_dir = project_dir

        # check group name
        if not self.group:
            raise ValueError('Group name must be specified')
        if not check_group_name(self.group):
            raise ValueError('Group name has invalid format')

        # check artifact name
        if not self.artifact:
            raise ValueError('Artifact name must be specified')
        if not check_artifact_name(self.artifact):
            raise ValueError('Artifact name has invalid format')

        # check version number
        if not self.version:
            raise ValueError('Version number must be specified')
        if not check_version_number(self.version):
            raise ValueError('Version number has invalid format')

        # check filenames
        if self.files:
            for file_path in self.files:
                if not file_path:
                    raise ValueError('Path cannot be empty')
                if not check_files_file_path(file_path):
                    raise ValueError('Path "%s" has invalid format' % file_path)

    @property
    def group_dir(self):
        """Returns absolute local path to the directory where all of a group's artifacts are stored."""
        return os.path.join(self.packages_dir, self.repository.type, self.repository.root, os.path.join(*self.group.split('.')))

    @property
    def artifact_archive_path(self):
        """Path to artifact's archive."""
        return os.path.join(self.group_dir, self.artifact + '-' + self.version + '.zip')

    def get_artifacts_dir(self, env=ENV_PRODUCTION):
        """Directory where all artifacts are unpacked."""
        return os.path.join(self.group_dir, env)

    def get_artifact_dir(self, env=ENV_PRODUCTION):
        """Directory for particular unpacked artifact; contains the data directory and the info.json file"""
        return os.path.join(self.get_artifacts_dir(env), self.artifact + '-' + self.version)

    def get_artifact_data_dir(self, env=ENV_PRODUCTION):
        """Directory containing the actual data of a particular unpacked artifact."""
        return os.path.join(self.get_artifact_dir(env), 'data')

    def get_artifact_info_path(self, env=ENV_PRODUCTION):
        """Path to artifact's info.json file."""
        return os.path.join(self.get_artifact_dir(env), 'info.json')

    def get_package_info(self):
        """Returns a package info if package is published locally or downloaded."""
        package_info = None

        for env in (self.ENV_LOCAL, self.ENV_PRODUCTION):
            info_path = self.get_artifact_info_path(env)
            if file_exists(info_path):
                with open(info_path) as f:
                    info = json.load(f)

                package_info = PackageInfo(info, (env == self.ENV_LOCAL))
                break

        return package_info

    def get_path(self, file_path: str = None):
        """Returns a path to the package directory
        or to a particular file from the package.

        If you are getting a path to a package directory (without specifying "file_path"):
            - if a working directory for the dependency is not specified, the absolute path
            for the central package directory will be returned
            - if the dependency configuration specifies a working directory and that
            directory exists and is not empty, the method will return a path to that working directory
            - if a working directory is specified, but is empty, the absolute path for the
            central package directory will be returned

        If you are getting a path to a file within the package ("file_path" is specified):
            - if a working directory for the dependency is not specified, the absolute path
            for the central directory will be returned
            - if the dependency configuration specifies only a working directory (without a files list)
            and the file exists in the working directory, the method will return that path
            - if the file doesn't exist in the working directory, the method will try to get
            the absolute path to the file from the central directory
            - if the dependency configuration also specifies a files list, a file list must
            contain the requested file path, otherwise the exception will be raised

        :param file_path: get a path to a particular file within the package
        :return: str
        """
        # convert relative path from windows format to linux one
        # because only linux format is accepted for file paths in "files"
        if file_path:
            file_path = file_path.replace('\\', '/')

        # return a working directory if "file_path" is not specified and the directory is not empty
        if self.working_dir and not file_path and not self.files:
            working_dir = os.path.normpath(os.path.join(self.project_dir, self.working_dir))
            if not is_dir_empty(working_dir):
                return working_dir

        # raise an error if "file_path" specified, but doesn't exist in the list of working files
        if self.working_dir and file_path and self.files and (file_path not in self.files):
            raise ValueError('File "%s" is not a part of the package "%s:%s"'
                             % (file_path, self.group, self.artifact))

        # return file path from a working directory if "file_path" is specified and the file exists
        if self.working_dir and file_path:
            res_path = os.path.normpath(os.path.join(self.project_dir, self.working_dir, file_path))
            if file_exists(res_path):
                return res_path

        # otherwise return absolute path
        package_info = self.get_package_info()
        if not package_info:
            raise ValueError('Package "%s:%s:%s" is not installed' % (self.group, self.artifact, self.version))

        # check that the file exists in the package
        if file_path and (file_path not in package_info.files):
            raise FileNotFoundError('File "%s" doesn\'t exist in the package "%s:%s:%s"'
                                    % (file_path, self.group, self.artifact, self.version))

        # get package data directory
        env = Dependency.ENV_LOCAL if package_info.local else Dependency.ENV_PRODUCTION
        data_dir = self.get_artifact_data_dir(env)

        # package path or file path
        res_path = os.path.normpath(os.path.join(data_dir, file_path)) if file_path else data_dir

        return res_path

    def update(self, rewrite_working_dir: bool = False, output: AbstractOutputWriter = None):
        """Downloads the package and updates the package's working directory."""
        if not output:
            output = NullOutputWriter()

        package_info = self.download(output)
        if not package_info or not self.working_dir:
            return

        # copy files to a working directory
        with output.indent():
            output.write('Copying files to the working directory "%s"...' % self.working_dir)

            with output.indent():
                # create a working directory if it doesn't exist
                working_dir = os.path.join(self.project_dir, self.working_dir)
                os.makedirs(working_dir, exist_ok=True)

                # get package data directory
                env = Dependency.ENV_LOCAL if package_info.local else Dependency.ENV_PRODUCTION
                data_dir = self.get_artifact_data_dir(env)

                if self.files:
                    # copy only specified files if they don't exist in a target directory
                    for filename in self.files:
                        if filename in package_info.files:
                            src_path = os.path.join(data_dir, filename)
                            dst_path = os.path.join(working_dir, filename)

                            # adding to working directory only files which don't exist
                            if not file_exists(dst_path):
                                copy_file(src_path, dst_path)
                                output.write('[+] "%s": file copied' % filename)
                            elif rewrite_working_dir:
                                copy_file(src_path, dst_path)
                                output.write('[+] "%s": file rewritten' % filename)
                            else:
                                output.write('[-] "%s": file already exists' % filename)
                        else:
                            output.write('[-] "%s": file doesn\'t exist in the package' % filename)
                else:
                    # copy all files only if a working directory is empty
                    if is_dir_empty(working_dir):
                        copy_dir(data_dir, working_dir)
                        output.write('[+] files copied to the "%s" directory' % self.working_dir)
                    elif rewrite_working_dir:
                        rmtree(working_dir)
                        copy_dir(data_dir, working_dir)
                        output.write('[+] directory "%s" was rewritten' % self.working_dir)
                    else:
                        output.write('[-] files not changed: directory "%s" is not empty' % self.working_dir)

    def publish(self, local: bool = False, rewrite_local: bool = False, output: AbstractOutputWriter = None) -> bool:
        """Publishes the package to the repository."""
        if not output:
            output = NullOutputWriter()

        # check if the package already exists on the local machine
        package_info = self.get_package_info()
        if package_info:
            if not package_info.local:
                output.write('[-] Version "%s" already exists in the repository' % self.version)
                return False
            elif not rewrite_local:
                output.write(
                    '[-] Version "%s" already exists locally. Use "-r" flag to rewrite this version.' % self.version)
                return False

        # paths for package
        artifact_dir = self.get_artifact_dir()
        local_artifact_dir = self.get_artifact_dir(Dependency.ENV_LOCAL)

        # build the package
        output.write('Building the package... ')

        with output.indent():
            try:
                tmp_artifact_dir = self._build()
            except Exception as e:
                output.write('[-] ' + str(e))
                return False

        # publish the package
        if local:
            output.write('Publishing the package locally... ')

            # move temporary directory to local one
            copy_dir(tmp_artifact_dir, local_artifact_dir)
            rmtree(tmp_artifact_dir)

            with output.indent():
                output.write('[+] Package "%s:%s:%s" was successfully published locally.' %
                             (self.group, self.artifact, self.version))
        else:
            output.write('Publishing the package... ')

            with output.indent():
                # upload a package
                driver = self.repository.driver

                try:
                    driver.upload_package(self.group, self.artifact, self.version, tmp_artifact_dir, output)
                except Exception as e:
                    rmtree(tmp_artifact_dir)  # remove building directory
                    output.write('[-] ' + str(e))
                    return False

                # move temporary directory to production one
                copy_dir(tmp_artifact_dir, artifact_dir)

                # remove building directory
                rmtree(tmp_artifact_dir)

                # remove local version of the same package if it exists
                if dir_exists(local_artifact_dir):
                    rmtree(local_artifact_dir)

                output.write('[+] Package "%s:%s:%s" was successfully published.' %
                             (self.group, self.artifact, self.version))

        # show published files
        package_info = self.get_package_info()

        output.write('\nPackage files:')
        with output.indent():
            for filename in package_info.files:
                output.write(filename)

        return True

    def download(self, output: AbstractOutputWriter = None):
        """Downloads a package.
        This method only puts the package to the central directory,
        without updating the package's working directory.
        """
        if not output:
            output = NullOutputWriter()

        output.write('Downloading package "%s:%s:%s"... ' % (self.group, self.artifact, self.version))

        with output.indent():
            # check if a package is already downloaded or published locally
            package_info = self.get_package_info()
            if package_info:
                if package_info.local:
                    output.write('[+] It\'s a locally published package')
                else:
                    output.write('[+] The package was already downloaded')

                return package_info

            # download dependency
            driver = self.repository.driver
            tmp_artifact_dir = self.get_artifact_dir(self.ENV_TMP)
            os.makedirs(tmp_artifact_dir, exist_ok=True)

            try:
                driver.download_package(self.group, self.artifact, self.version, tmp_artifact_dir, output)
            except Exception as e:
                output.write('[-] ' + str(e))
                return None

            # TODO: check "tmp_dir" contains info.json file, format is correct and a list of files matches "data" directory

            # move temporary directory to production one
            artifact_dir = self.get_artifact_dir(self.ENV_PRODUCTION)
            copy_dir(tmp_artifact_dir, artifact_dir)
            rmtree(tmp_artifact_dir)

            package_info = self.get_package_info()

            output.write('[+] The package was successfully downloaded')

        return package_info

    def _build(self):
        """Builds package."""
        if not self.working_dir:
            raise ValueError('Package doesn\'t have working directory')

        # working directory
        working_dir = os.path.join(self.project_dir, self.working_dir)
        if not dir_exists(working_dir):
            raise ValueError('Working directory doesn\'t exist')

        # package paths
        artifact_dir = self.get_artifact_dir(self.ENV_TMP)
        info_path = self.get_artifact_info_path(self.ENV_TMP)
        data_dir = self.get_artifact_data_dir(self.ENV_TMP)

        # remove artifact directory if it exists
        if dir_exists(artifact_dir):
            rmtree(artifact_dir)

        # create artifact data directory
        os.makedirs(data_dir, exist_ok=True)

        # copy files to package data directory
        if self.files:
            for filename in self.files:
                src_path = os.path.join(working_dir, filename)
                if not file_exists(src_path):
                    raise FileNotFoundError('File "%s" doesn\'t exist in the working directory' % filename)

                copy_file(src_path, os.path.join(data_dir, filename))
        else:
            copy_dir(working_dir, data_dir)

        # get the list of copied files
        files = []
        for cur_dir, directories, filenames in os.walk(data_dir):
            relative_dir = cur_dir.replace(data_dir, '').lstrip(os.sep)
            for filename in filenames:
                files.append(os.path.join(relative_dir, filename))

        # create info.json file
        package_info = OrderedDict([
            ('group', self.group),
            ('artifact', self.artifact),
            ('version', self.version),
            ('files', files),
            ('name', self.name),
            ('description', self.description),
            ('hash', get_dir_hash(data_dir))
        ])
        with open(info_path, 'w+') as f:
            json.dump(package_info, f, indent=2)

        return artifact_dir
