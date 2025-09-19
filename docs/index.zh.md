# 羽盒

**羽盒 (yuhe)** 是一个交互式的 3D 边界盒 (bounding box, bbox) 选择工具。
它可以在网格 (mesh) 上快速拟合边界盒，并导出判别函数代码，用于检测点是否在边界盒内部。

<video width=100% autoplay muted loop>
  <source src="[[url.videos]]/media/movies/demo.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

## 界面功能

![gui]([[url.prefix]]/media/gui.jpg)

1. **平移**：调整边界盒的位置。
2. **旋转**（单位：度）：绕 XYZ 轴旋转边界盒。
3. **缩放**：设置边界盒长、宽、高。
4. **Padding**：在边界盒恰好包围所选点后，向外额外扩展的距离。
5. **显示/隐藏拖拽小工具**。
6. **重置**：恢复初始状态。
7. **代码语言选择**：选择生成判别函数的语言（C++ / Python）。
8. **生成判别函数代码**：在终端输出判别函数的代码。
9. **点的数据类型**：选择 `double` 或 `float`。
10. **坐标变量名**：以英文逗号分隔（如 `x,y,z`）。

## 使用方法

- 按住 **Shift + 鼠标左键** 点击模型，可在模型上标记点。
- 按住 **Shift + 鼠标左键** 再次点击已标记的点，可删除该点。
- 当标记点数量大于 3 个时，程序会自动计算能够包围这些点的边界盒。
- 可以在右侧面板调整参数以满足需求。
- 点击 **Generate Code**，将在终端生成判别函数代码，可复制粘贴到自己的项目中。
