from typing import Literal

import numpy as np

from yuhe.geometry_utils import compute_transform_matrix

CANONICAL_MIN_V = np.array([-0.5, -0.5, -0.5])
CANONICAL_MAX_V = np.array([0.5, 0.5, 0.5])


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
    transform = compute_transform_matrix(tx, ty, tz, rx, ry, rz, sx, sy, sz, padding)
    inverse_transform = np.linalg.inv(transform)

    # Format rows into plain C arrays
    inv_transform_rows = []
    for row in inverse_transform:
        row_str = ", ".join(f"{val:.10f}" for val in row)
        inv_transform_rows.append("    { " + row_str + " }")
    inv_transform_str = "{\n" + ",\n".join(inv_transform_rows) + "\n};"

    return f"""
auto is_point_in_box = []({point_type} {x_coord}, {point_type} {y_coord}, {point_type} {z_coord}) -> bool {{
    {point_type} inv_transform[4][4] = {inv_transform_str}

    {point_type} p_world[4] = {{{x_coord}, {y_coord}, {z_coord}, 1.0}};
    {point_type} p_local[4];
    for(int i=0;i<4;++i) {{
        p_local[i] = 0;
        for(int j=0;j<4;++j) {{
            p_local[i] += inv_transform[i][j] * p_world[j];
        }}
    }}

    return p_local[0] >= {CANONICAL_MIN_V[0]:.10f} && p_local[0] <= {CANONICAL_MAX_V[0]:.10f} &&
           p_local[1] >= {CANONICAL_MIN_V[1]:.10f} && p_local[1] <= {CANONICAL_MAX_V[1]:.10f} &&
           p_local[2] >= {CANONICAL_MIN_V[2]:.10f} && p_local[2] <= {CANONICAL_MAX_V[2]:.10f};
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
    x_coord, y_coord, z_coord = coord_names
    transform = compute_transform_matrix(tx, ty, tz, rx, ry, rz, sx, sy, sz, padding)
    inverse_transform = np.linalg.inv(transform)

    inv_str = "    inv_transform = np.array([\n"
    for row in inverse_transform:
        inv_str += "        [" + ", ".join(f"{val:.10f}" for val in row) + "],\n"
    inv_str = inv_str.rstrip(",\n") + "\n    ])\n"

    return f"""
import numpy as np

def is_point_in_box({x_coord}: float, {y_coord}: float, {z_coord}: float) -> bool:
{inv_str}
    p_world = np.array([{x_coord}, {y_coord}, {z_coord}, 1.0])
    p_local = inv_transform @ p_world
    return ({CANONICAL_MIN_V[0]:.10f} <= p_local[0] <= {CANONICAL_MAX_V[0]:.10f}) and \\
           ({CANONICAL_MIN_V[1]:.10f} <= p_local[1] <= {CANONICAL_MAX_V[1]:.10f}) and \\
           ({CANONICAL_MIN_V[2]:.10f} <= p_local[2] <= {CANONICAL_MAX_V[2]:.10f})
"""
