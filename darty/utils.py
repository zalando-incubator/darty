import os
import errno
import hashlib
from shutil import rmtree, copytree, copyfile


def check_path(path):
    """Creates a directory if it doesn't exist."""
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise exception


def get_input(message: str, default_value=None):
    """Gets user's input or uses a default value."""
    value = input(message)
    if not value:
        if default_value is not None:
            value = default_value
        else:
            print('Value is required', flush=True)
            value = get_input(message)

    return value


def dir_exists(path: str):
    return os.path.exists(path) or os.path.isdir(path)


def file_exists(path: str):
    return os.path.exists(path) or os.path.isfile(path)


def is_dir_empty(path: str):
    return not dir_exists(path) or not len(os.listdir(path))


def copy_file(src_path, dst_path):
    """Copies a file.
    Creates necessary directories if they didn't exists.
    """
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    copyfile(src_path, dst_path)


def copy_dir(src_dir, dst_dir):
    """Copies a directory.
    Destination directory will be removed before copying.
    """
    rmtree(dst_dir, True)
    res = copytree(src_dir, dst_dir)

    return res


def list_dir_files(dir_path):
    for cur_dir, directories, filenames in os.walk(dir_path):
        rel_dir = os.path.relpath(cur_dir, dir_path)
        for filename in filenames:
            yield os.path.join(rel_dir, filename)


def get_dir_hash(path: str):
    """Gets SHA1 hash of the directory.

    :param path:
    :return:
    """
    sha_hash = hashlib.sha1()
    if not dir_exists(path):
        raise ValueError('Directory "%s" doesn\'t exist' % dir)

    for cur_dir, directories, filenames in os.walk(path):
        for filename in filenames:
            file_path = os.path.join(cur_dir, filename)

            # add filename to a hash
            relative_path = os.path.relpath(file_path, path).replace('\\', '/')
            sha_hash.update(relative_path.encode('utf-8'))

            # add file content to a hash
            with open(file_path, 'rb') as f:
                while True:
                    buf = f.read(4096)
                    if not buf:
                        break

                    sha_hash.update(hashlib.sha1(buf).hexdigest().encode('utf-8'))

    return sha_hash.hexdigest()


def convert_path_w2u(path):
    """Converts path from Windows style to Unix style.
    If the path was already written in Unix style it remains unchanged.
    """
    return path.replace('\\', '/')
