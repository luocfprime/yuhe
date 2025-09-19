# import numpy as np
# import pytest
# import trimesh
#
# from yuhe.code_generators import generate_python_function, CANONICAL_MIN_V, CANONICAL_MAX_V
# from yuhe.geometry_utils import compute_transform_matrix, fit_obb_to_points
#
#
# def generate_test_grid(bounds=(-2, 2), num_points_per_dim=10):
#     """Generates a 3D grid of points for testing."""
#     lin = np.linspace(bounds[0], bounds[1], num_points_per_dim)
#     xx, yy, zz = np.meshgrid(lin, lin, lin)
#     points = np.vstack([xx.ravel(), yy.ravel(), zz.ravel()]).T
#     return points
#
#
# @pytest.mark.parametrize(
#     "box_config",
#     [
#         # Axis-aligned, default size
#         {"tx": 0, "ty": 0, "tz": 0, "rx": 0, "ry": 0, "rz": 0, "sx": 1, "sy": 1, "sz": 1, "padding": 0.0},
#         # Translated
#         {"tx": 1, "ty": 0.5, "tz": -0.5, "rx": 0, "ry": 0, "rz": 0, "sx": 1, "sy": 1, "sz": 1, "padding": 0.0},
#         # Scaled
#         {"tx": 0, "ty": 0, "tz": 0, "rx": 0, "ry": 0, "rz": 0, "sx": 2, "sy": 0.5, "sz": 1.5, "padding": 0.0},
#         # Rotated (around Z-axis)
#         {"tx": 0, "ty": 0, "tz": 0, "rx": 0, "ry": 0, "rz": 45, "sx": 1, "sy": 1, "sz": 1, "padding": 0.0},
#         # Rotated (complex)
