# 桌宠开源调研

- https://github.com/LGaben/Desktop-Pets ：MIT，Python/PyQt5，透明无边框、漫步、托盘及点击互动。阅读README和pet/base_pet.py，借鉴交互设计，未复制实现代码或第三方角色素材。
- https://github.com/kokoronoka/desktopPet ：Electron透明无边框桌宠，提供自主漫步和拖动。当前未核实可复用许可证，因此未复制其代码。

本项目现使用PySide6透明桌宠与Qt助手界面；旧Tk模型仅保留兼容后端，界面不再以Tk为宿主。原文旧路线：使用Tk/Pillow宿主，保留桌面API和资料功能，避免迁移导致功能丢失。当前无边框主体只显示透明狐狸娘；单击摸头、拖动移动、右键操作、双击打开助手；自主漫步不调用AI。原始图集用内置imagegen重绘，导入时隔离每格最大主体并加透明边距。


## 0.8 GIS 与 Agent 参考
- QGIS：https://github.com/qgis/QGIS 。完整GIS与qgis_process命令行，GPL；本机尚未安装，计划作为独立可选后端，不把第三方代码改署名为fox。
- GeoAgent：https://github.com/iamtekson/GeoAgent 。自然语言选择Processing工具及保存模型；其自身代码MIT，运行于QGIS时还需遵守组合许可。本轮只核对说明并参考流程，未复制或安装。
- QGIS MCP：https://github.com/Aaa2122/QGIS-MCP 。参考任务上下文、取消与诊断机制；尚未接入本机。
- GeoPandas：https://github.com/geopandas/geopandas 。BSD-3-Clause，空间表与投影转换；尚未作为运行依赖。
- Shapely：https://github.com/shapely/shapely 。本次实验在开发Python环境中独立运算，非打包EXE依赖；单侧缓冲强制平头，不能冒充ArcMap RIGHT+ROUND。
- Rasterio：https://github.com/rasterio/rasterio 。开发环境检查栅格地理参考；未把未知PRJ编造成EPSG。
- 多Agent参考CrewAI、AutoGen、LangGraph角色交接与状态设计，本项目的轻量实现不依赖这些框架。

上述“参考”“开发环境使用”“可选接入”不等于已安装或已运行第三方完整项目。原项目许可证与版权不由fox的MIT声明替代。
