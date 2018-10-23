import zipfile
import os


def get_dir_files(dir_path: str):
    """Returns paths for all files in the directory."""
    for cur_dir, directories, filenames in os.walk(dir_path):
        cur_rel_dir = os.path.relpath(cur_dir, dir_path)
        if cur_rel_dir == '.':
            cur_rel_dir = ''

        for filename in filenames:
            yield os.path.join(cur_rel_dir, filename)


def unpack_archive(archive_path: str, dst_dir: str, delete_file: bool = False):
    """Unpacks downloaded package."""
    archive = zipfile.ZipFile(archive_path)
    archive.extractall(dst_dir)

    if delete_file:
        os.remove(archive_path)


def pack_archive(src_dir: str, archive_path: str):
    """Creates a new package."""

    # get all paths before an archive is created
    file_paths = list(get_dir_files(src_dir))

    # create an archive
    archive = zipfile.ZipFile(archive_path, 'w')

    for file_path in file_paths:
        archive.write(os.path.join(src_dir, file_path), arcname=file_path)

    archive.close()
