
import numpy as np


def validate_mesh(mesh):
    """
    Validate a Shap-E triangular mesh before export.

    Returns:
        dict: Validation status and mesh statistics.
    Raises:
        ValueError: If the mesh is invalid.
    """

    if mesh is None:
        raise ValueError("Mesh cannot be None.")

    vertices = np.asarray(mesh.verts)
    faces = np.asarray(mesh.faces)

    if vertices.ndim != 2 or vertices.shape[1] != 3:
        raise ValueError("Vertices must have shape (N, 3).")

    if faces.ndim != 2 or faces.shape[1] != 3:
        raise ValueError("Faces must have shape (M, 3).")

    if len(vertices) == 0:
        raise ValueError("Mesh contains no vertices.")

    if len(faces) == 0:
        raise ValueError("Mesh contains no faces.")

    if not np.isfinite(vertices).all():
        raise ValueError("Mesh contains invalid vertex coordinates.")

    if not np.issubdtype(faces.dtype, np.integer):
        if not np.isfinite(faces).all():
            raise ValueError("Face indices contain invalid values.")
        if not np.equal(faces, np.floor(faces)).all():
            raise ValueError("Face indices must be integers.")

    faces = faces.astype(np.int64)

    if faces.min() < 0 or faces.max() >= len(vertices):
        raise ValueError("Face references an invalid vertex index.")

    return {
        "valid": True,
        "vertex_count": int(len(vertices)),
        "face_count": int(len(faces)),
        "status": "Mesh validation successful"
    }
