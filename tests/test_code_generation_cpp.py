import platform
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pytest

from tests.utils import generate_test_grid, make_box_mesh, plot_box_and_points
from yuhe.code_generators import generate_cpp_function
from yuhe.geometry_utils import compute_transform_matrix


def build_executable(cpp_function_code: str, tmp_path: Path) -> Path:
    """
    Fills a C++ template, creates a Ninja build file, compiles the executable,
    and returns its path.
    """
    template_path = Path("tests/template/main.cpp")
    template_code = template_path.read_text()
    final_cpp_code = template_code.replace("{{IS_POINT_IN_BOX_FUNCTION}}", cpp_function_code)

    cpp_file_path = tmp_path / "generated.cpp"
    # Determine executable name based on OS
    exe_name = "point_in_box.exe" if platform.system() == "Windows" else "point_in_box"
    exe_file_path = tmp_path / exe_name

    cpp_file_path.write_text(final_cpp_code)

    # Create a simple build.ninja file
    ninja_build_content = f"""
rule compile
  command = g++ -std=c++17 $in -o $out
  description = Compiling $in

build {exe_name}: compile {cpp_file_path.name}
"""
    ninja_file_path = tmp_path / "build.ninja"
    ninja_file_path.write_text(ninja_build_content)

    print(f"Compiling C++ executable using Ninja in {tmp_path}")

    try:
        # Run ninja from the temporary directory
        subprocess.run(  # noqa: S603
            ["ninja", "-f", str(ninja_file_path.name)],  # noqa: S607
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
        )
        print("Ninja compilation successful.")
    except subprocess.CalledProcessError as e:
        print(f"Ninja compilation failed. STDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
        raise
    except FileNotFoundError:
        pytest.skip("Ninja not found. Skipping C++ test that requires Ninja.")

    return exe_file_path


def run_exe(exe: Path, points: np.ndarray, point_type: str, coord_names: list[str]) -> np.ndarray:
    results = []
    for p_idx, (x, y, z) in enumerate(points):
        # Format arguments for C++ executable based on coord_names
        # Note: The main.cpp template expects x, y, z in order, so we
        # simply pass the values in order regardless of coord_names.
        # The generated C++ function itself is responsible for mapping them correctly.
        args = [str(x), str(y), str(z)]
        try:
            res = subprocess.run(  # noqa: S603
                [str(exe), *args],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,  # Add a timeout to prevent hanging tests
            )
            results.append(res.stdout.strip() == "1")
        except subprocess.CalledProcessError as e:
            print(f"Executable failed for point {p_idx} ({x}, {y}, {z}). STDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
            raise
        except subprocess.TimeoutExpired:
            print(f"Executable timed out for point {p_idx} ({x}, {y}, {z}).")
            raise
    return np.array(results)


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
@pytest.mark.parametrize("point_type", ["double", "float"])
@pytest.mark.parametrize("coord_names", [["x", "y", "z"], ["a", "b", "c"]])
def test_generated_cpp_function_matches_trimesh(box_config, point_type, coord_names):
    """
    Tests that the C++ generated function (from yuhe.code_generators)
    accurately determines if points are inside a bounding box, by comparing
    against trimesh's `contains` method. The C++ executable is built using Ninja.
    """
    # Create a temporary directory for the executable and ninja files
    with tempfile.TemporaryDirectory() as tmpdir_name:
        tmp_path = Path(tmpdir_name)

        grid_points = generate_test_grid(bounds=(-3, 3), num_points_per_dim=10)  # Expand grid for better coverage
        transform = compute_transform_matrix(**box_config)

        # Use trimesh to get ground truth for point inclusion
        box_mesh = make_box_mesh(transform)
        gt = box_mesh.contains(grid_points)

        cpp_func_code = generate_cpp_function(**box_config, point_type=point_type, coord_names=coord_names)

        # Build the C++ executable using Ninja
        exe = build_executable(cpp_func_code, tmp_path)

        # Run the compiled C++ executable for each point
        cpp_results = run_exe(exe, grid_points, point_type, coord_names)

        # Compare results
        mismatches = cpp_results != gt
        num_mismatches = mismatches.sum()

        if mismatches.any():
            plot_box_and_points(
                box_mesh,
                grid_points,
                gt,
                mismatches,
                filename=f"debug_box_{box_config['rx']}_{box_config['ry']}_{box_config['rz']}.png",
            )
            pytest.fail(
                f"Test failed for config={box_config}, point_type={point_type}, coord_names={coord_names}\n"
                f"{num_mismatches} mismatches found.\n"
                f"Mismatching points:\n{grid_points[mismatches]}\n"
                f"Ground truth:\n{gt[mismatches]}\n"
                f"C++ results:\n{cpp_results[mismatches]}"
            )
