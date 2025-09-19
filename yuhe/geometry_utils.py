import numpy as np


def normalize_angle(a: float) -> float:
    """Normalizes an angle to be within (-180, 180]."""
    a %= 360.0
    return a - 360.0 if a > 180 else a


def rotation_matrix(rx: float, ry: float, rz: float) -> np.ndarray:
    """Generates a 4x4 rotation matrix from Euler angles (in degrees)."""
    rx, ry, rz = map(np.deg2rad, [rx, ry, rz])
    Rx = np.array([
        [1, 0, 0, 0],
        [0, np.cos(rx), -np.sin(rx), 0],
        [0, np.sin(rx), np.cos(rx), 0],
        [0, 0, 0, 1],
    ])
    Ry = np.array([
        [np.cos(ry), 0, np.sin(ry), 0],
        [0, 1, 0, 0],
        [-np.sin(ry), 0, np.cos(ry), 0],
        [0, 0, 0, 1],
    ])
    Rz = np.array([
        [np.cos(rz), -np.sin(rz), 0, 0],
        [np.sin(rz), np.cos(rz), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ])
    return Rz @ Ry @ Rx


def translation_matrix(tx: float, ty: float, tz: float) -> np.ndarray:
    """Generates a 4x4 translation matrix."""
    T = np.eye(4)
    T[:3, 3] = [tx, ty, tz]
    return T


def decompose_matrix(
    M: np.ndarray,
) -> tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]:
    """Decomposes a 4x4 affine matrix into translation, rotation (Euler degrees), and scale components."""
    tx, ty, tz = M[:3, 3]
    basis = M[:3, :3]
    sx, sy, sz = (np.linalg.norm(basis[:, i]) for i in range(3))

    R = np.zeros((3, 3))
    if sx > 1e-8:
        R[:, 0] = basis[:, 0] / sx
    if sy > 1e-8:
        R[:, 1] = basis[:, 1] / sy
    if sz > 1e-8:
        R[:, 2] = basis[:, 2] / sz

    ry = np.arcsin(-R[2, 0])
    if abs(np.cos(ry)) > 1e-8:
        rx = np.arctan2(R[2, 1], R[2, 2])
        rz = np.arctan2(R[1, 0], R[0, 0])
    else:
        rx = np.arctan2(-R[1, 2], R[1, 1])
        rz = 0.0

    rx, ry, rz = map(np.rad2deg, [rx, ry, rz])
    rx, ry, rz = map(normalize_angle, [rx, ry, rz])
    return (tx, ty, tz), (rx, ry, rz), (sx, sy, sz)  # type: ignore [return-value]
