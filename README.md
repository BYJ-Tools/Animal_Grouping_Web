# 🐾 实验动物均衡分组系统 (Web版)

这是一个基于 Streamlit 开发的网页端工具，用于实验室动物实验前期的随机且均衡的分组。

## ✨ 核心功能
*   **多指标均衡**：支持自定义 Excel 表格中的任意数量指标（如体重、血糖、心率等）。
*   **指标权重设置**：可为不同指标分配 0 到 1 的权重（1为最重要，0为不考虑），满足复杂实验设计需求。
*   **一键智能分配**：内置启发式优化算法，能在几秒内将动物（如小鼠/大鼠）完美分为若干组，保证组间各项指标均值无显著差异。
*   **结果直接导出**：自动生成包含分组结果及各组均值统计的 Excel 文件，方便直接用于实验记录。

## 🚀 在线使用
无需安装任何软件，直接用浏览器打开以下链接即可使用：
👉 **[点击这里进入分组系统](https://animalgroupingweb-2fdpfcxsqqvphwmtyy76sh.streamlit.app)**

## 💻 本地运行 (针对开发者)
如果你希望在本地运行或修改代码：
1. 克隆本仓库：`git clone https://github.com/BYJ-Tools/Animal_Grouping_Web.git`
2. 安装依赖：`pip install -r requirements.txt`
3. 运行应用：`streamlit run Grouping_web_app.py`

## 📄 开源协议
本项目基于 MIT License 开源。
