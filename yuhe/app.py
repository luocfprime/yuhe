import logging
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal

import numpy as np
import polyscope as ps
import polyscope.imgui as psim
import trimesh

from yuhe.code_generators import (
    generate_cpp_function,
    generate_python_function,
)
from yuhe.config import AutoSaveConfig
from yuhe.geometry_utils import (
    CANONICAL_BOX_FACES,
    CANONICAL_BOX_VERTICES,
    compute_transform_matrix,
    decompose_matrix,
    fit_obb_to_points,
    normalize_angle,
)
from yuhe.ui_utils import ui_combo, ui_item_width, ui_tree_node

logger = logging.getLogger(__name__)

DEFAULT_BOX_PARAM = MappingProxyType({
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
})


class PolyscopeApp:
    def __init__(self, mesh_path: str | Path):
        try:
            self.config = AutoSaveConfig(".yuhe.json")
            logger.debug("Loaded config from .yuhe.json")
        except FileNotFoundError:
            logger.debug("Using default config.")
            self.config = AutoSaveConfig(".yuhe.json")

        logger.debug(f"Loading mesh from {mesh_path}")
        self.input_mesh = trimesh.load_mesh(mesh_path)

        ps.set_program_name("Yuhe")
        ps.set_print_prefix("[Yuhe][Polyscope] ")
        ps.set_ground_plane_mode("shadow_only")
        ps.set_up_dir("z_up")
        ps.set_front_dir("x_front")

        ps.init()

        ps.register_surface_mesh("input_mesh", self.input_mesh.vertices, self.input_mesh.faces, color=(0.7, 0.7, 0.9))

        # State for picked points
        self.picked_points: list[np.ndarray] = []
        self.picked_cloud = None

        # Register box
        self.box_mesh = ps.register_surface_mesh(
            "box", CANONICAL_BOX_VERTICES, CANONICAL_BOX_FACES, color=(1.0, 0.0, 0.0), transparency=0.4
        )
        self._update_box_geometry()

    @property
    def box_params(self) -> dict[str, float]:
        keys = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "padding"]
        for k in keys:
            if k not in self.config:
                self.config[k] = DEFAULT_BOX_PARAM[k]

        return {k: self.config[k] for k in keys}

    def update_box_params(self, params: dict[str, float]):
        for k, v in params.items():
            self.config[k] = float(v)

    @property
    def selected_language(self) -> Literal["cpp", "python"]:
        if "selected_language" not in self.config:
            self.config["selected_language"] = "cpp"
        return self.config["selected_language"]

    @selected_language.setter
    def selected_language(self, lang: Literal["cpp", "python"]):
        self.config["selected_language"] = lang

    @property
    def coord_names(self) -> list[str]:
        if "coord_names" not in self.config:
            self.config["coord_names"] = ["x", "y", "z"]
        return self.config["coord_names"]

    @coord_names.setter
    def coord_names(self, names: list[str]):
        self.config["coord_names"] = names

    @property
    def cpp_point_type(self) -> Literal["double", "float"]:
        if "cpp_point_type" not in self.config:
            self.config["cpp_point_type"] = "double"
        return self.config["cpp_point_type"]

    @cpp_point_type.setter
    def cpp_point_type(self, point_type: Literal["double", "float"]):
        self.config["cpp_point_type"] = point_type

    def _update_box_geometry(self):
        transform = compute_transform_matrix(**self.box_params)
        self.box_mesh.set_transform(transform)

    def _fit_bbox_to_points_and_update_params(self, points: np.ndarray) -> bool:
        try:
            fitted_params = fit_obb_to_points(points, padding=self.box_params["padding"])
            self.update_box_params(fitted_params)
        except ValueError as e:
            if "At least 4 points are required to fit an OBB" not in str(e):
                logger.warning(f"Could not fit bounding box: {e}")
            return False
        except Exception:
            logger.exception("Unexpected error during OBB fitting.")
            return False
        else:
            return True

    def _handle_mouse_picking(self, io: Any):
        if io.MouseClicked[0] and io.KeyShift:
            pick_res = ps.pick(screen_coords=io.MousePos)

            if pick_res.is_hit and pick_res.structure_name == "picked_points":
                if self.picked_points:
                    idx = pick_res.local_index
                    if 0 <= idx < len(self.picked_points):
                        self.picked_points.pop(idx)

            elif pick_res.is_hit and pick_res.structure_name == "input_mesh":
                self.picked_points.append(pick_res.position.copy())

            if self.picked_cloud is not None:
                ps.remove_point_cloud("picked_points", error_if_absent=False)
                self.picked_cloud = None
            if self.picked_points:
                pts_np = np.array(self.picked_points)
                self.picked_cloud = ps.register_point_cloud("picked_points", pts_np, color=(0.2, 1.0, 0.2), radius=0.01)
                if self._fit_bbox_to_points_and_update_params(pts_np):
                    self._update_box_geometry()

    def _handle_transform_sliders(self):
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
                self.update_box_params({k: normalize_angle(val) if k in ["rx", "ry", "rz"] else val})
                self._update_box_geometry()

    def _handle_padding_slider(self):
        changed, val = psim.DragFloat("padding", self.box_params["padding"], 0.01, 0, 1000)
        if changed:
            self.update_box_params({"padding": max(0.0, val)})
            if self.picked_points:
                pts_np = np.array(self.picked_points)
                if self._fit_bbox_to_points_and_update_params(pts_np):
                    self._update_box_geometry()
            else:
                self._update_box_geometry()

    def _ui_language_selector(self):
        with ui_combo("Language", self.selected_language) as expanded:
            if expanded:
                if psim.Selectable("cpp", self.selected_language == "cpp")[0]:
                    self.selected_language = "cpp"
                if psim.Selectable("python", self.selected_language == "python")[0]:
                    self.selected_language = "python"

    def _ui_enable_gizmo(self):
        changed, enable_gizmo = psim.Checkbox("Enable Gizmo", self.box_mesh.get_transform_gizmo_enabled())
        if changed:
            self.box_mesh.set_transform_gizmo_enabled(enable_gizmo)

    def _ui_show_points(self):
        changed, show_points = psim.Checkbox(
            "Show Points", self.picked_cloud is not None and self.picked_cloud.is_enabled()
        )
        if changed:
            if self.picked_cloud is None:  # Do nothing if not exist
                return
            self.picked_cloud.set_enabled(show_points)

    def _ui_reset(self):
        if psim.Button("Reset"):
            # 1. reset box
            self.update_box_params(dict(DEFAULT_BOX_PARAM))
            self._update_box_geometry()

            # 2. reset points
            self.picked_points = []
            if self.picked_cloud:
                ps.remove_point_cloud("picked_points", error_if_absent=False)

    def _ui_cpp_options(self):
        if self.selected_language == "cpp":
            with ui_combo("Point Type", self.cpp_point_type) as expanded:
                if expanded:
                    if psim.Selectable("double", self.cpp_point_type == "double")[0]:
                        self.cpp_point_type = "double"
                    if psim.Selectable("float", self.cpp_point_type == "float")[0]:
                        self.cpp_point_type = "float"

    def _ui_coord_names(self):
        coord_str = ",".join(self.coord_names)
        changed, new_val = psim.InputText("Coord Names (x,y,z)", coord_str)
        if changed:
            names = [c.strip() for c in new_val.split(",")[:3]]
            while len(names) < 3:
                names.append(["x", "y", "z"][len(names)])
            self.coord_names = names[:3]

    def _ui_generate_button(self):
        psim.SameLine()
        if psim.Button("Generate Code"):
            params = {k: self.box_params[k] for k in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "padding"]}
            if self.selected_language == "cpp":
                code = generate_cpp_function(**params, point_type=self.cpp_point_type, coord_names=self.coord_names)
            else:
                code = generate_python_function(**params, coord_names=self.coord_names)

            print("\nGenerated Code:")
            print(code)

    def _ui_code_generation(self):
        """Main wrapper for code generation controls."""
        with ui_tree_node("Generate Point Inclusion Function") as expanded:
            if not expanded:
                return
            with ui_item_width(100):
                self._ui_language_selector()
                self._ui_generate_button()

            self._ui_cpp_options()
            self._ui_coord_names()

    def callback(self) -> None:
        io = psim.GetIO()
        self._handle_mouse_picking(io)

        current_ps_transform = self.box_mesh.get_transform()
        (tx, ty, tz), (rx, ry, rz), (sx_e, sy_e, sz_e) = decompose_matrix(current_ps_transform)
        self.update_box_params({
            "tx": tx,
            "ty": ty,
            "tz": tz,
            "rx": rx,
            "ry": ry,
            "rz": rz,
            "sx": max(0.01, sx_e - 2 * self.box_params["padding"]),
            "sy": max(0.01, sy_e - 2 * self.box_params["padding"]),
            "sz": max(0.01, sz_e - 2 * self.box_params["padding"]),
        })

        self._handle_transform_sliders()
        self._handle_padding_slider()
        self._ui_enable_gizmo()
        psim.SameLine()
        self._ui_show_points()
        psim.SameLine()
        self._ui_reset()
        self._ui_code_generation()
        self._update_box_geometry()

    def run(self):
        ps.set_user_callback(self.callback)
        ps.show()
