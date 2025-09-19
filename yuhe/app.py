import logging
from pathlib import Path

import numpy as np
import polyscope as ps
import polyscope.imgui as psim
import trimesh

from yuhe.geometry_utils import decompose_matrix, normalize_angle, rotation_matrix, translation_matrix

logger = logging.getLogger(__name__)


class PolyscopeApp:
    def __init__(self, mesh_path: str | Path):
        logger.debug(f"Loading mesh from {mesh_path}")
        self.input_mesh = trimesh.load_mesh(mesh_path)

        ps.set_program_name("Yuhe")
        ps.set_print_prefix("[Yuhe][Polyscope] ")
        ps.set_ground_plane_mode("shadow_only")
        ps.set_up_dir("z_up")
        ps.set_front_dir("x_front")

        ps.init()

        ps.register_surface_mesh("input_mesh", self.input_mesh.vertices, self.input_mesh.faces, color=(0.7, 0.7, 0.9))

        # State
        self.picked_points: list[int] = []
        self.picked_cloud = None

        # Box setup
        self.box_params = {
            "tx": 0.0,
            "ty": 0.0,
            "tz": 0.0,
            "rx": 0.0,
            "ry": 0.0,
            "rz": 0.0,
            "sx": 1.0,
            "sy": 1.0,
            "sz": 1.0,
            "padding": 0.0,
        }

        self.base_vertices = np.array(
            [
                [-0.5, -0.5, -0.5],
                [0.5, -0.5, -0.5],
                [0.5, 0.5, -0.5],
                [-0.5, 0.5, -0.5],
                [-0.5, -0.5, 0.5],
                [0.5, -0.5, 0.5],
                [0.5, 0.5, 0.5],
                [-0.5, 0.5, 0.5],
            ],
            dtype=float,
        )

        self.cube_faces = np.array([
            [0, 1, 2],
            [0, 2, 3],
            [4, 5, 6],
            [4, 6, 7],
            [0, 1, 5],
            [0, 5, 4],
            [2, 3, 7],
            [2, 7, 6],
            [1, 2, 6],
            [1, 6, 5],
            [0, 3, 7],
            [0, 7, 4],
        ])

        self.box_vertices = self.base_vertices.copy()
        self.box_mesh = ps.register_surface_mesh(
            "box", self.box_vertices, self.cube_faces, color=(1.0, 0.0, 0.0), transparency=0.4
        )

    def _update_box_geometry(self):
        scale = np.array([self.box_params["sx"], self.box_params["sy"], self.box_params["sz"]])
        self.box_vertices[:] = self.base_vertices * scale
        self.box_mesh.update_vertex_positions(self.box_vertices)

        R = rotation_matrix(self.box_params["rx"], self.box_params["ry"], self.box_params["rz"])
        T = translation_matrix(self.box_params["tx"], self.box_params["ty"], self.box_params["tz"])
        self.box_mesh.set_transform(T @ R)

    def _fit_bbox_to_points(self, points: np.ndarray):
        if len(points) < 4:
            return False
        if np.linalg.matrix_rank(points - points.mean(axis=0)) < 3:
            return False

        cloud = trimesh.points.PointCloud(points)

        try:
            hull = cloud.convex_hull
            obb = hull.bounding_box_oriented
        except Exception:
            # fallback to axis-aligned if hull/obb fails
            logger.exception("Falling back to bounding_box")
            obb = cloud.bounding_box

        transform = obb.primitive.transform
        extents = obb.primitive.extents
        pad = self.box_params["padding"]

        self.box_params.update({
            "tx": transform[0, 3],
            "ty": transform[1, 3],
            "tz": transform[2, 3],
            "rx": 0.0,
            "ry": 0.0,
            "rz": 0.0,
            "sx": extents[0] + 2 * pad,
            "sy": extents[1] + 2 * pad,
            "sz": extents[2] + 2 * pad,
        })

        R = transform[:3, :3]
        ry = np.arcsin(-R[2, 0])
        if abs(np.cos(ry)) > 1e-8:
            rx = np.arctan2(R[2, 1], R[2, 2])
            rz = np.arctan2(R[1, 0], R[0, 0])
        else:
            rx = np.arctan2(-R[1, 2], R[1, 1])
            rz = 0.0
        rx, ry, rz = map(np.rad2deg, [rx, ry, rz])
        self.box_params.update({
            "rx": normalize_angle(rx),
            "ry": normalize_angle(ry),
            "rz": normalize_angle(rz),
        })
        return True

    def _handle_mouse_picking(self, io):
        if io.MouseClicked[0] and io.KeyShift:  # left-mouse + shift key
            pick_res = ps.pick(screen_coords=io.MousePos)

            if pick_res.is_hit and pick_res.structure_name == "picked_points":  # case 1. select picked points
                idx = pick_res.local_index
                if 0 <= idx < len(self.picked_points):
                    self.picked_points.pop(idx)

            elif pick_res.is_hit and pick_res.structure_name == "input_mesh":  # case 2. select on input mesh
                self.picked_points.append(pick_res.position.copy())

            if self.picked_cloud is not None:
                ps.remove_point_cloud("picked_points", error_if_absent=False)
                self.picked_cloud = None
            if len(self.picked_points) > 0:
                pts_np = np.array(self.picked_points)
                self.picked_cloud = ps.register_point_cloud("picked_points", pts_np, color=(0.2, 1.0, 0.2), radius=0.01)
                if self._fit_bbox_to_points(pts_np):
                    self._update_box_geometry()

    def _handle_transform_sliders(self):
        # sliders for transform & scale
        for k, s in {
            "tx": 0.01,
            "ty": 0.01,
            "tz": 0.01,
            "rx": 1.0,
            "ry": 1.0,
            "rz": 1.0,
            "sx": 0.01,
            "sy": 0.01,
            "sz": 0.01,
        }.items():
            changed, val = psim.DragFloat(k, self.box_params[k], s, -1000, 1000)
            if changed:
                self.box_params[k] = normalize_angle(val) if k in ["rx", "ry", "rz"] else val

    def _handle_padding_slider(self):
        changed, val = psim.DragFloat("padding", self.box_params["padding"], 0.01, 0, 1000)
        if changed:
            self.box_params["padding"] = max(0.0, val)
            if len(self.picked_points) > 0:
                pts_np = np.array(self.picked_points)
                if self._fit_bbox_to_points(pts_np):
                    self._update_box_geometry()

    def callback(self) -> None:
        io = psim.GetIO()

        self._handle_mouse_picking(io)

        affine = self.box_mesh.get_transform()
        (tx, ty, tz), (rx, ry, rz), _ = decompose_matrix(affine)
        self.box_params.update({"tx": tx, "ty": ty, "tz": tz, "rx": rx, "ry": ry, "rz": rz})

        self._handle_transform_sliders()
        self._handle_padding_slider()

        self._update_box_geometry()

    def run(self):
        ps.set_user_callback(self.callback)
        ps.show()
