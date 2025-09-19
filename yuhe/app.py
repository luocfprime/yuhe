from pathlib import Path
import trimesh

import numpy as np
import polyscope as ps
import polyscope.imgui as psim

class PolyscopeApp:
    def __init__(self, mesh_path: str | Path):
        self.mesh = trimesh.load_mesh(mesh_path)

        ps.set_program_name("Yumo")
        ps.set_print_prefix("[Yumo][Polyscope] ")
        ps.set_ground_plane_mode("shadow_only")
        ps.set_up_dir("z_up")
        ps.set_front_dir("x_front")

        ps.init()

    def callback(self) -> None:
        ...

    def run(self):
        ps.set_user_callback(self.callback)
        ps.show()
