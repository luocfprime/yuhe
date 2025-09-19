import matplotlib.pyplot as plt
import numpy as np
import pytest
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from yuhe.code_generators import generate_python_function
from yuhe.geometry_utils import CANONICAL_BOX_FACES, CANONICAL_BOX_VERTICES, compute_transform_matrix


def plot_box_and_points(box_mesh, points, inside_mask, mismatch_mask, filename="box_debug.png"):
    """Visualize trimesh box and points, save to file."""
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection="3d")

    # Plot trimesh box faces
    for face in box_mesh.faces:
        tri = box_mesh.vertices[face]
        poly = Poly3DCollection([tri], color="lightblue", alpha=0.3, edgecolor="k")
        ax.add_collection3d(poly)

    # Plot points classified as inside by trimesh
    inside = points[inside_mask]
    outside = points[~inside_mask]

    ax.scatter(outside[:, 0], outside[:, 1], outside[:, 2], c="gray", s=10, alpha=0.5, label="Outside")
    ax.scatter(inside[:, 0], inside[:, 1], inside[:, 2], c="green", s=15, alpha=0.8, label="Inside")

    # Highlight mismatches
    if mismatch_mask.any():
        mismatches = points[mismatch_mask]
        ax.scatter(mismatches[:, 0], mismatches[:, 1], mismatches[:, 2], c="red", marker="x", s=60, label="Mismatch")

    # Niceties
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.legend()
    ax.set_title("Box vs Grid Points")

    # Auto scale
    all_pts = np.vstack([points, box_mesh.vertices])
    mins, maxs = all_pts.min(0), all_pts.max(0)
    ax.set_xlim(mins[0], maxs[0])
    ax.set_ylim(mins[1], maxs[1])
    ax.set_zlim(mins[2], maxs[2])

    fig.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close(fig)
    print(f"Visualization saved -> {filename}")


def generate_test_grid(bounds=(-2, 2), num_points_per_dim=10):
    """Generates a 3D grid of points for testing."""
    lin = np.linspace(bounds[0], bounds[1], num_points_per_dim)
    xx, yy, zz = np.meshgrid(lin, lin, lin)
    points = np.vstack([xx.ravel(), yy.ravel(), zz.ravel()]).T
    return points


def make_box_mesh(transform: np.ndarray) -> trimesh.Trimesh:
    # Use the canonical vertices, convert to homogeneous coords
    verts_h = np.c_[CANONICAL_BOX_VERTICES, np.ones(len(CANONICAL_BOX_VERTICES))]  # shape (8, 4)
    verts_transformed = (transform @ verts_h.T).T[:, :3]
    return trimesh.Trimesh(vertices=verts_transformed, faces=CANONICAL_BOX_FACES, process=False)


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
def test_generated_python_function_matches_trimesh(box_config):
    grid_points = generate_test_grid(bounds=(-2, 2), num_points_per_dim=8)

    # Build trimesh Box: extents are sx,sy,sz; transform already has padding applied
    transform = compute_transform_matrix(**box_config)
    box_mesh = make_box_mesh(transform)

    gt = box_mesh.contains(grid_points)

    # Generate Python function dynamically and exec
    code = generate_python_function(**box_config, coord_names=["x", "y", "z"])
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
