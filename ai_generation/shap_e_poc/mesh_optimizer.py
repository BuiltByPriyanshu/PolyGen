
import numpy as np
from collections import Counter


def optimize_mesh(mesh):
    """
    Analyse and clean a triangular mesh.

    Removes duplicate vertices, duplicate faces and degenerate
    triangles. Reports edge topology, connected components,
    and isolated vertex statistics.
    """

    vertices = np.asarray(mesh.verts, dtype=np.float64)
    raw_faces = np.asarray(mesh.faces)

    # Validate vertex dimensions.
    if vertices.ndim != 2 or vertices.shape[1] != 3:
        raise ValueError("Invalid vertex dimensions.")

    # Validate face dimensions.
    if raw_faces.ndim != 2 or raw_faces.shape[1] != 3:
        raise ValueError("Invalid face dimensions.")

    # Validate face indices before integer conversion.
    if not np.issubdtype(raw_faces.dtype, np.number):
        raise ValueError("Face indices must be numeric.")

    if not np.isfinite(raw_faces).all():
        raise ValueError("Face indices contain non-finite values.")

    if not np.equal(raw_faces, np.floor(raw_faces)).all():
        raise ValueError("Face indices must be integers.")

    faces = raw_faces.astype(np.int64)

    # Validate vertex coordinates.
    if not np.isfinite(vertices).all():
        raise ValueError("Mesh contains non-finite coordinates.")

    if len(vertices) == 0 or len(faces) == 0:
        raise ValueError("Mesh is empty.")

    if faces.min() < 0 or faces.max() >= len(vertices):
        raise ValueError("Invalid face vertex index.")

    original_vertices = len(vertices)
    original_faces = len(faces)

    # Count isolated vertices before optimization.
    referenced_vertices = np.unique(faces.flatten())

    isolated_vertices_before = (
        original_vertices - len(referenced_vertices)
    )

    isolated_vertex_percentage = (
        isolated_vertices_before / original_vertices
    ) * 100.0

    # Remove duplicate vertices.
    unique_vertices, inverse = np.unique(
        vertices, axis=0, return_inverse=True
    )
    faces = inverse[faces]
    vertices = unique_vertices

    # Remove repeated-index faces.
    distinct = (
        (faces[:, 0] != faces[:, 1]) &
        (faces[:, 1] != faces[:, 2]) &
        (faces[:, 0] != faces[:, 2])
    )
    faces = faces[distinct]

    # Remove zero-area and near-zero-area triangles.
    a = vertices[faces[:, 1]] - vertices[faces[:, 0]]
    b = vertices[faces[:, 2]] - vertices[faces[:, 0]]
    areas = 0.5 * np.linalg.norm(np.cross(a, b), axis=1)

    scale = max(float(np.ptp(vertices, axis=0).max()), 1.0)
    valid_area = areas > (1e-12 * scale * scale)
    faces = faces[valid_area]

    # Remove duplicate faces regardless of winding.
    canonical_faces = np.sort(faces, axis=1)
    _, unique_indices = np.unique(
        canonical_faces, axis=0, return_index=True
    )
    faces = faces[np.sort(unique_indices)]

    if len(faces) == 0:
        raise ValueError("No valid faces remain after cleanup.")

    # Remove vertices no longer referenced by faces.
    used_vertices, inverse = np.unique(
        faces.flatten(), return_inverse=True
    )
    vertices = vertices[used_vertices]
    faces = inverse.reshape(-1, 3)

    # Count isolated vertices after cleanup.
    isolated_vertices_after = len(vertices) - len(
        np.unique(faces.flatten())
    )

    # Analyse mesh edge topology.
    edges = np.concatenate([
        faces[:, [0, 1]],
        faces[:, [1, 2]],
        faces[:, [2, 0]]
    ])

    edges = np.sort(edges, axis=1)
    edge_counts = Counter(map(tuple, edges.tolist()))

    boundary_edges = sum(
        count == 1 for count in edge_counts.values()
    )

    manifold_edges = sum(
        count == 2 for count in edge_counts.values()
    )

    non_manifold_edges = sum(
        count > 2 for count in edge_counts.values()
    )

    total_edges = len(edge_counts)

    # Calculate connected components using shared edges.
    parent = list(range(len(faces)))
    rank = [0] * len(faces)

    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(first, second):
        root_first = find(first)
        root_second = find(second)

        if root_first == root_second:
            return

        if rank[root_first] < rank[root_second]:
            root_first, root_second = root_second, root_first

        parent[root_second] = root_first

        if rank[root_first] == rank[root_second]:
            rank[root_first] += 1

    edge_to_face = {}

    for face_index, face in enumerate(faces):
        face_edges = [
            tuple(sorted((int(face[0]), int(face[1])))),
            tuple(sorted((int(face[1]), int(face[2])))),
            tuple(sorted((int(face[2]), int(face[0]))))
        ]

        for edge in face_edges:
            if edge in edge_to_face:
                union(face_index, edge_to_face[edge])
            else:
                edge_to_face[edge] = face_index

    component_sizes = Counter(
        find(face_index) for face_index in range(len(faces))
    )

    connected_components = len(component_sizes)
    largest_component_faces = max(component_sizes.values())

    isolated_components = sum(
        size == 1 for size in component_sizes.values()
    )

    # Calculate surface area.
    a = vertices[faces[:, 1]] - vertices[faces[:, 0]]
    b = vertices[faces[:, 2]] - vertices[faces[:, 0]]

    surface_area = float(
        np.sum(0.5 * np.linalg.norm(np.cross(a, b), axis=1))
    )

    return {
        "vertices": vertices,
        "faces": faces,
        "quality_report": {
            "original_vertices": int(original_vertices),
            "optimized_vertices": int(len(vertices)),
            "original_faces": int(original_faces),
            "optimized_faces": int(len(faces)),
            "removed_vertices": int(original_vertices - len(vertices)),
            "removed_faces": int(original_faces - len(faces)),
            "isolated_vertices_before_cleanup": int(
                isolated_vertices_before
            ),
            "isolated_vertex_percentage": float(
                isolated_vertex_percentage
            ),
            "isolated_vertices_after_cleanup": int(
                isolated_vertices_after
            ),
            "surface_area": surface_area,
            "total_edges": int(total_edges),
            "boundary_edges": int(boundary_edges),
            "manifold_edges": int(manifold_edges),
            "non_manifold_edges": int(non_manifold_edges),
            "connected_components": int(connected_components),
            "largest_component_faces": int(largest_component_faces),
            "isolated_components": int(isolated_components),
            "optimization_status": "completed"
        }
    }
