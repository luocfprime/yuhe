import json
from typing import Literal

import numpy as np

from yuhe.geometry_utils import compute_transform_matrix

CANONICAL_MIN_V = np.array([-0.5, -0.5, -0.5])
CANONICAL_MAX_V = np.array([0.5, 0.5, 0.5])

# read only constants
CANONICAL_MIN_V.setflags(write=False)
CANONICAL_MAX_V.setflags(write=False)


def generate_cpp_function(
    tx: float,
    ty: float,
    tz: float,
    rx: float,
    ry: float,
    rz: float,
    sx: float,
    sy: float,
    sz: float,
    padding: float,
    point_type: Literal["double", "float"],
    coord_names: list[str],
) -> str:
    x_coord, y_coord, z_coord = coord_names

    # 1. Build transform matrix (world transform of OBB)
    transform = compute_transform_matrix(tx, ty, tz, rx, ry, rz, sx, sy, sz, padding)

    # 2. Extract center from transform (translation part)
    center = transform[:3, 3]

    # 3. Extract axis direction (rotation part, 3x3 part of transform),
    # normalize them because scaling is removed
    u = transform[:3, 0] / np.linalg.norm(transform[:3, 0])
    v = transform[:3, 1] / np.linalg.norm(transform[:3, 1])
    w = transform[:3, 2] / np.linalg.norm(transform[:3, 2])

    # 4. Half extents = scale/2 (with padding)
    hx = (sx / 2.0) + padding
    hy = (sy / 2.0) + padding
    hz = (sz / 2.0) + padding

    params = {
        "tx": tx,
        "ty": ty,
        "tz": tz,
        "rx": rx,
        "ry": ry,
        "rz": rz,
        "sx": sx,
        "sy": sy,
        "sz": sz,
        "padding": padding,
    }
    params_json = json.dumps(params, ensure_ascii=False)

    # Format vectors
    def fmt_arr(arr):
        return ", ".join(f"{v:.10f}" for v in arr)

    return f"""
auto is_point_in_box = []({point_type} {x_coord}, {point_type} {y_coord}, {point_type} {z_coord}) -> bool {{
    // Parameters: {params_json}
    // Represent OBB as center + axis vectors + half extents

    const {point_type} C[3] = {{ {center[0]:.10f}, {center[1]:.10f}, {center[2]:.10f} }};
    const {point_type} U[3] = {{ {fmt_arr(u)} }};
    const {point_type} V[3] = {{ {fmt_arr(v)} }};
    const {point_type} W[3] = {{ {fmt_arr(w)} }};
    const {point_type} hx = {hx:.10f};
    const {point_type} hy = {hy:.10f};
    const {point_type} hz = {hz:.10f};

    // Compute vector from center to point
    const {point_type} dx = {x_coord} - C[0];
    const {point_type} dy = {y_coord} - C[1];
    const {point_type} dz = {z_coord} - C[2];

    // Dot products onto each axis
    const {point_type} proj_x = dx*U[0] + dy*U[1] + dz*U[2];
    if (std::abs(proj_x) > hx) return false;

    const {point_type} proj_y = dx*V[0] + dy*V[1] + dz*V[2];
    if (std::abs(proj_y) > hy) return false;

    const {point_type} proj_z = dx*W[0] + dy*W[1] + dz*W[2];
    if (std::abs(proj_z) > hz) return false;

    return true;
}};
"""


def generate_python_function(
    tx: float,
    ty: float,
    tz: float,
    rx: float,
    ry: float,
    rz: float,
    sx: float,
    sy: float,
    sz: float,
    padding: float,
    coord_names: list[str],
) -> str:
    import json

    import numpy as np

    x_coord, y_coord, z_coord = coord_names

    # 1. Compute transform (world transform of OBB)
    transform = compute_transform_matrix(tx, ty, tz, rx, ry, rz, sx, sy, sz, padding)

    # 2. Extract center from translation part
    center = transform[:3, 3]

    # 3. Extract axis directions (rotation with scaling applied)
    u = transform[:3, 0] / np.linalg.norm(transform[:3, 0])
    v = transform[:3, 1] / np.linalg.norm(transform[:3, 1])
    w = transform[:3, 2] / np.linalg.norm(transform[:3, 2])

    # 4. Half-extents = scale/2 + padding
    hx = (sx / 2.0) + padding
    hy = (sy / 2.0) + padding
    hz = (sz / 2.0) + padding

    params = {
        "tx": tx,
        "ty": ty,
        "tz": tz,
        "rx": rx,
        "ry": ry,
        "rz": rz,
        "sx": sx,
        "sy": sy,
        "sz": sz,
        "padding": padding,
    }
    params_json = json.dumps(params, ensure_ascii=False)

    def fmt(arr):
        return ", ".join(f"{x:.10f}" for x in arr)

    return f"""
import numpy as np

def is_point_in_box({x_coord}: float, {y_coord}: float, {z_coord}: float) -> bool:
    # Parameters: {params_json}
    # OBB represented as center + axis vectors + half extents

    C = np.array([{center[0]:.10f}, {center[1]:.10f}, {center[2]:.10f}])
    U = np.array([{fmt(u)}])  # unit axis x
    V = np.array([{fmt(v)}])  # unit axis y
    W = np.array([{fmt(w)}])  # unit axis z
    hx, hy, hz = {hx:.10f}, {hy:.10f}, {hz:.10f}

    # Vector from center to point
    d = np.array([{x_coord}, {y_coord}, {z_coord}]) - C

    # Projection on each axis and half-extent check
    proj_x = np.dot(d, U)
    if abs(proj_x) > hx:
        return False

    proj_y = np.dot(d, V)
    if abs(proj_y) > hy:
        return False

    proj_z = np.dot(d, W)
    if abs(proj_z) > hz:
        return False

    return True
"""
