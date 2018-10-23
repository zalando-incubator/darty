import re


def check_group_name(group: str):
    regexp = '^[a-z][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*$'
    pattern = re.compile(regexp)
    return pattern.match(group)


def check_artifact_name(artifact: str):
    regexp = '^[a-z][a-z0-9_-]*[a-z0-9]$'
    pattern = re.compile(regexp)
    return pattern.match(artifact)


def check_version_number(version: str):
    regexp = '^v?[0-9]+(\.[0-9]+){0,2}([a-z-][a-z0-9-][a-z0-9]*)?$'
    pattern = re.compile(regexp)
    return pattern.match(version)


def check_files_file_path(file_path: str):
    regexp = '^[a-z0-9\.-_]([a-z0-9-/_]+\.?)*[a-z0-9-_]$'
    pattern = re.compile(regexp)
    return pattern.match(file_path)


def check_repository_type(repository_type: str):
    regexp = '^[a-z0-9_]*$'
    pattern = re.compile(regexp)
    return pattern.match(repository_type)


def check_repository_root(root: str):
    regexp = '^[a-z0-9_-]*$'
    pattern = re.compile(regexp)
    return pattern.match(root)
