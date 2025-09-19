# yuhe

**yuhe** is an interactive 3D bounding box (bbox) selection tool.
It allows you to quickly fit a bbox on a mesh and export discriminator function code to check whether a point lies inside the bbox.

<video width=100% autoplay muted loop>
  <source src="[[url.videos]]/media/movies/demo.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Interface

![gui]([[url.prefix]]/media/gui.jpg)

1. **BBox translation**
2. **BBox rotation** (unit: degrees)
3. **BBox scaling** (length, width, height)
4. **Padding**: extra margin added after the bbox tightly encloses the selected points
5. **Show/Hide transform gizmo**
6. **Reset**
7. **Language choice** for the discriminator function (C++ / Python)
8. **Generate code** for the discriminator function (printed in the command-line terminal)
9. **Data type** for points (`double` / `float`)
10. **Variable names** for point coordinates, separated by commas

## How to use

- Hold **Shift + Left Mouse Button** to click on the model and mark points.
- Hold **Shift + Left Mouse Button** on a marked point again to remove it.
- When 3 or more points are marked, a bbox that encloses these points will be automatically computed.
- Adjust parameters in the right-side panel as needed.
- Click **Generate Code** to output the function code, then copy-paste it into your own project.
