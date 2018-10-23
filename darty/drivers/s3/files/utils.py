import os


def get_dir_files(dir_path: str):
    """Returns paths for all files in the directory."""
    for cur_dir, directories, filenames in os.walk(dir_path):
        cur_rel_dir = os.path.relpath(cur_dir, dir_path)
        if cur_rel_dir == '.':
            cur_rel_dir = ''

        for filename in filenames:
            yield os.path.join(cur_rel_dir, filename)
