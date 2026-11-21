
import numpy as np
from collections import Counter


def optimize_mesh(mesh):
    """
    Analyse and clean a triangular mesh.
    Returns cleaned vertices, faces and quality statistics.
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
    # Analyse mesh edge topology.
    edges = np.concatenate([
        faces[:, [0, 1]],
        faces[:, [1, 2]],
        faces[:, [2, 0]]
    ])

    # Normalize edge direction so shared edges are counted together.
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
            "surface_area": surface_area,
            "total_edges": int(total_edges),
            "boundary_edges": int(boundary_edges),
            "manifold_edges": int(manifold_edges),
            "non_manifold_edges": int(non_manifold_edges),
            "optimization_status": "completed"
        }
    }
