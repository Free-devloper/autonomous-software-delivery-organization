from collections import deque

from autonomous_sdo_api.planning.models import (
    CyclicDependencyError,
    DagEdge,
    PlanningError,
    WorkPackage,
)


def validate_and_sort_dag(
    work_packages: list[WorkPackage],
    edges: list[DagEdge],
) -> list[str]:
    """Validate DAG invariants and return work package IDs in topological execution order."""
    package_ids = {wp.id for wp in work_packages}

    # Verify all edges refer to existing packages
    for edge in edges:
        if edge.from_package_id not in package_ids:
            raise PlanningError(f"Edge source '{edge.from_package_id}' does not exist.")
        if edge.to_package_id not in package_ids:
            raise PlanningError(f"Edge target '{edge.to_package_id}' does not exist.")
        if edge.from_package_id == edge.to_package_id:
            raise CyclicDependencyError(
                f"Self-referencing cycle detected on package '{edge.from_package_id}'."
            )

    # In-degree tracking for Kahn's algorithm
    in_degree: dict[str, int] = {wp_id: 0 for wp_id in package_ids}
    adj: dict[str, list[str]] = {wp_id: [] for wp_id in package_ids}

    # Also account for explicit dependencies on WorkPackage models
    for wp in work_packages:
        for dep in wp.dependencies:
            if dep not in package_ids:
                raise PlanningError(
                    f"Package '{wp.id}' references non-existent dependency '{dep}'."
                )
            if dep == wp.id:
                raise CyclicDependencyError(
                    f"Self-referencing cycle detected on package '{wp.id}'."
                )
            adj[dep].append(wp.id)
            in_degree[wp.id] += 1

    for edge in edges:
        adj[edge.from_package_id].append(edge.to_package_id)
        in_degree[edge.to_package_id] += 1

    queue: deque[str] = deque([wp_id for wp_id, deg in in_degree.items() if deg == 0])
    sorted_order: list[str] = []

    while queue:
        curr = queue.popleft()
        sorted_order.append(curr)

        for neighbor in adj[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(sorted_order) != len(package_ids):
        raise CyclicDependencyError("Circular dependency detected in work package DAG.")

    return sorted_order
