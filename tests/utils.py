import matplotlib.pyplot as plt
import numpy as np
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from yuhe.geometry_utils import CANONICAL_BOX_FACES, CANONICAL_BOX_VERTICES


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

    plt.show()

    fig.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close(fig)
    print(f"Visualization saved -> {filename}")


def generate_test_grid(bounds=(-2, 2), num_points_per_dim=10, perturbance=0.01):
    """Generates a 3D grid of points for testing, with small random perturbations."""
    lin = np.linspace(bounds[0], bounds[1], num_points_per_dim)
    xx, yy, zz = np.meshgrid(lin, lin, lin, indexing="ij")
    points = np.vstack([xx.ravel(), yy.ravel(), zz.ravel()]).T  # shape (N^3, 3)

    # add perturbations of same shape
    pert = perturbance * np.random.randn(*points.shape)
    points += pert

    return points


def make_box_mesh(transform: np.ndarray) -> trimesh.Trimesh:
    # Use the canonical vertices, convert to homogeneous coords
    verts_h = np.c_[CANONICAL_BOX_VERTICES, np.ones(len(CANONICAL_BOX_VERTICES))]  # shape (8, 4)
    verts_transformed = (transform @ verts_h.T).T[:, :3]
    return trimesh.Trimesh(vertices=verts_transformed, faces=CANONICAL_BOX_FACES, process=False)
