import numpy as np
import pytest

from tests.utils import generate_test_grid, make_box_mesh, plot_box_and_points
from yuhe.code_generators import generate_python_function
from yuhe.geometry_utils import compute_transform_matrix


@pytest.mark.parametrize(
    "box_config",
    [
        # Axis-aligned, default size
        {"tx": 0, "ty": 0, "tz": 0, "rx": 0, "ry": 0, "rz": 0, "sx": 1, "sy": 1, "sz": 1, "padding": 0.0},
        # Translated
        {"tx": 1, "ty": 0.5, "tz": -0.5, "rx": 0, "ry": 0, "rz": 0, "sx": 1, "sy": 1, "sz": 1, "padding": 0.0},
        # Scaled
        {"tx": 0, "ty": 0, "tz": 0, "rx": 0, "ry": 0, "rz": 0, "sx": 2, "sy": 0.5, "sz": 1.5, "padding": 0.0},
        # Rotated (around Z-axis)
        {"tx": 0, "ty": 0, "tz": 0, "rx": 0, "ry": 0, "rz": 45, "sx": 1, "sy": 1, "sz": 1, "padding": 0.0},
        # Padded
        {"tx": 0, "ty": 0, "tz": 0, "rx": 0, "ry": 0, "rz": 0, "sx": 1, "sy": 1, "sz": 1, "padding": 2.0},
        # Rotated (complex)
        {
            "tx": 0.5,
            "ty": -0.5,
            "tz": 0.5,
            "rx": 30,
            "ry": 45,
            "rz": 10,
            "sx": 1.5,
            "sy": 0.5,
            "sz": 1.0,
            "padding": 3.0,
        },
    ],
)
@pytest.mark.parametrize("coord_names", [["x", "y", "z"], ["a", "b", "c"]])
def test_generated_python_function_matches_trimesh(box_config, coord_names):
    grid_points = generate_test_grid(bounds=(-2, 2), num_points_per_dim=8)

    # Build trimesh Box: extents are sx,sy,sz; transform already has padding applied
    transform = compute_transform_matrix(**box_config)
    box_mesh = make_box_mesh(transform)

    gt = box_mesh.contains(grid_points)

    # Generate Python function dynamically and exec
    code = generate_python_function(**box_config, coord_names=coord_names)
    ns = {}
    exec(code, ns)  # noqa: S102
    fn = ns["is_point_in_box"]

    results = np.array([fn(*p) for p in grid_points])
    mismatches = results != gt.astype(bool)

    if mismatches.any():
        plot_box_and_points(
            box_mesh,
            grid_points,
            gt,
            mismatches,
            filename=f"debug_box_{box_config['rx']}_{box_config['ry']}_{box_config['rz']}.png",
        )
        pytest.fail(f"Found {mismatches.sum()} mismatches for config {box_config}. See visualization image.")
