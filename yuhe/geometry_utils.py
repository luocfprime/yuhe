import logging

import numpy as np
import trimesh

logger = logging.getLogger(__name__)


def normalize_angle(a: float) -> float:
    """Normalizes an angle to be within (-180, 180]."""
    a %= 360.0
    return a - 360.0 if a > 180 else a


def compute_transform_matrix(
    tx: float,
    ty: float,
    tz: float,
    rx: float,
    ry: float,
    rz: float,  # degrees
    sx: float,
    sy: float,
    sz: float,
    padding: float = 0.0,
) -> np.ndarray:
    """
    Computes a 4x4 affine transformation matrix from box parameters.
    Order of operations: Scale -> Rotate -> Translate.
    """
    # Apply scaling (including padding)
    scale_x = sx + 2 * padding
    scale_y = sy + 2 * padding
    scale_z = sz + 2 * padding
    scale_mat = np.diag([scale_x, scale_y, scale_z, 1.0])

    # Apply rotation (Euler angles in degrees)
    rx_rad, ry_rad, rz_rad = map(np.deg2rad, [rx, ry, rz])

    Rx = np.array([
        [1, 0, 0, 0],
        [0, np.cos(rx_rad), -np.sin(rx_rad), 0],
        [0, np.sin(rx_rad), np.cos(rx_rad), 0],
        [0, 0, 0, 1],
    ])
    Ry = np.array([
        [np.cos(ry_rad), 0, np.sin(ry_rad), 0],
        [0, 1, 0, 0],
        [-np.sin(ry_rad), 0, np.cos(ry_rad), 0],
        [0, 0, 0, 1],
    ])
    Rz = np.array([
        [np.cos(rz_rad), -np.sin(rz_rad), 0, 0],
        [np.sin(rz_rad), np.cos(rz_rad), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ])
    rotation_mat = Rz @ Ry @ Rx  # Standard ZYX Euler order

    # Apply translation
    translation_mat = np.eye(4)
    translation_mat[:3, 3] = [tx, ty, tz]

    # Combine: T * R * S
    return translation_mat @ rotation_mat @ scale_mat


def decompose_matrix(
    M: np.ndarray,
) -> tuple[
    tuple[float, float, float],  # translation
    tuple[float, float, float],  # rotation (degrees)
    tuple[float, float, float],  # scale (extents)
]:
    """Decomposes a 4x4 affine matrix into translation, rotation (Euler degrees), and scale components."""
    tx, ty, tz = M[:3, 3]
    basis = M[:3, :3]

    # Calculate scale from the basis vectors' norms
    sx = np.linalg.norm(basis[:, 0])
    sy = np.linalg.norm(basis[:, 1])
    sz = np.linalg.norm(basis[:, 2])

    R = np.zeros((3, 3))
    if sx > 1e-8:
        R[:, 0] = basis[:, 0] / sx
    if sy > 1e-8:
        R[:, 1] = basis[:, 1] / sy
    if sz > 1e-8:
        R[:, 2] = basis[:, 2] / sz

    # Extract Euler angles (ZYX order)
    # Handle singularity when ry is +/- 90 degrees
    ry_rad = np.arcsin(-R[2, 0])
    if abs(np.cos(ry_rad)) > 1e-8:
        rx_rad = np.arctan2(R[2, 1], R[2, 2])
        rz_rad = np.arctan2(R[1, 0], R[0, 0])
    else:
        # Gimbal lock: assume rz = 0, distribute rotation between rx and ry
        rx_rad = np.arctan2(-R[1, 2], R[1, 1])
        rz_rad = 0.0  # Can be arbitrary, choose 0 for consistency

    rx, ry, rz = map(np.rad2deg, [rx_rad, ry_rad, rz_rad])
    rx, ry, rz = map(normalize_angle, [rx, ry, rz])

    return (tx, ty, tz), (rx, ry, rz), (sx, sy, sz)  # type: ignore[return-value]


def fit_obb_to_points(points: np.ndarray, padding: float = 0.0) -> dict:
    """
    Fits an oriented bounding box (OBB) to a set of points and returns
    its parameters (translation, rotation, scale) and padding.
    """
    if len(points) < 4:
        raise ValueError("At least 4 points are required to fit an OBB.")
    if np.linalg.matrix_rank(points - points.mean(axis=0)) < 3:
        raise ValueError("Points must not be coplanar or collinear.")

    cloud = trimesh.points.PointCloud(points)

    try:
        hull = cloud.convex_hull
        obb = hull.bounding_box_oriented
    except Exception:
        # Fallback to axis-aligned if hull/obb fails (less descriptive but robust)
        logger.exception("Warning: Falling back to axis-aligned bounding_box.")
        obb = cloud.bounding_box

    transform = obb.primitive.transform
    extents = obb.primitive.extents

    (tx, ty, tz), (rx, ry, rz), _ = decompose_matrix(transform)

    # trimesh.primitives.Box takes 'extents' as side lengths.
    # Our sx, sy, sz in box_params are also treated as side lengths (scaling factors from unit cube).
    # So we use obb.primitive.extents directly.
    return {
        "tx": tx,
        "ty": ty,
        "tz": tz,
        "rx": rx,
        "ry": ry,
        "rz": rz,
        "sx": extents[0],
        "sy": extents[1],
        "sz": extents[2],
        "padding": padding,  # The padding is added later in `compute_transform_matrix`
    }
