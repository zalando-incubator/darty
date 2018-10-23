from darty.dependency_manager import DependencyManager


def get_dependencies_by_name(manager: DependencyManager, group: str, artifact: str):
    """Searches dependencies by group and artifact."""
    if group and artifact:
        dependency = manager.get_dependency_by_name(group, artifact)
        if not dependency:
            raise ValueError('Package with group=%s and artifact=%s not found' % (group, artifact))
        dependencies = [dependency]
    elif artifact:
        dependencies = manager.search_dependency_by_artifact(artifact)
        if not dependencies:
            raise ValueError('Package with artifact=%s not found' % artifact)
    else:
        dependencies = list(manager.dependencies.values())

    return dependencies
