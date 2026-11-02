# 桌宠开源调研

- https://github.com/LGaben/Desktop-Pets ：MIT，Python/PyQt5，透明无边框、漫步、托盘及点击互动。阅读README和pet/base_pet.py，借鉴交互设计，未复制实现代码或第三方角色素材。
- https://github.com/kokoronoka/desktopPet ：Electron透明无边框桌宠，提供自主漫步和拖动。当前未核实可复用许可证，因此未复制其代码。

本项目继续使用已有Tk/Pillow宿主，保留桌面API和资料功能，避免迁移导致功能丢失。当前无边框主体只显示透明狐狸娘；单击摸头、拖动移动、右键操作、双击打开助手；自主漫步不调用AI。原始图集用内置imagegen重绘，导入时隔离每格最大主体并加透明边距。
