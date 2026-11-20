
import numpy as np
import pytest
from types import SimpleNamespace

from ai_generation.shap_e_poc.mesh_optimizer import optimize_mesh


def create_mesh(vertices, faces):
    return SimpleNamespace(
        verts=np.array(vertices, dtype=float),
        faces=np.array(faces)
    )


def test_valid_mesh_is_accepted():
    mesh = create_mesh(
        [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
        [[0, 1, 2]]
    )
    result = optimize_mesh(mesh)

    assert len(result["vertices"]) == 3
    assert len(result["faces"]) == 1
    assert result["quality_report"]["optimization_status"] == "completed"


def test_duplicate_vertices_are_removed():
    mesh = create_mesh(
        [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 0]],
        [[0, 1, 2]]
    )
    result = optimize_mesh(mesh)

    assert len(result["vertices"]) == 3
    assert result["quality_report"]["removed_vertices"] == 1


def test_duplicate_faces_are_removed():
    mesh = create_mesh(
        [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
        [[0, 1, 2], [2, 1, 0]]
    )
    result = optimize_mesh(mesh)

    assert len(result["faces"]) == 1
    assert result["quality_report"]["removed_faces"] == 1


def test_degenerate_faces_are_removed():
    mesh = create_mesh(
        [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
        [[0, 1, 2], [0, 0, 1]]
    )
    result = optimize_mesh(mesh)

    assert len(result["faces"]) == 1


def test_invalid_face_indices_are_rejected():
    mesh = create_mesh(
        [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
        [[0, 1, 5]]
    )

    with pytest.raises(ValueError, match="Invalid face vertex index"):
        optimize_mesh(mesh)


def test_non_finite_vertices_are_rejected():
    mesh = create_mesh(
        [[0, 0, 0], [1, 0, 0], [float("nan"), 1, 0]],
        [[0, 1, 2]]
    )

    with pytest.raises(ValueError, match="non-finite"):
        optimize_mesh(mesh)


def test_empty_mesh_is_rejected():
    mesh = create_mesh(
        np.empty((0, 3)),
        np.empty((0, 3), dtype=int)
    )

    with pytest.raises(ValueError, match="empty"):
        optimize_mesh(mesh)


def test_fractional_face_indices_are_rejected():
    mesh = create_mesh(
        [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
        [[0, 1.5, 2]]
    )

    with pytest.raises(ValueError, match="Face indices must be integers"):
        optimize_mesh(mesh)


def test_non_finite_face_indices_are_rejected():
    mesh = create_mesh(
        [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
        [[0, float("nan"), 2]]
    )

    with pytest.raises(ValueError, match="non-finite"):
        optimize_mesh(mesh)
