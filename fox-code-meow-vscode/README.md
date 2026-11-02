# fox · 陪伴小窝 v0.7.1

按用户确认的奶油色狐狸手账方案实现。作者 fox，新增源码MIT许可；第三方依赖保留各自许可声明。

## 本机使用

- 桌面：运行fox狐狸娘-0.7.1.exe。角色透明无边框，可走动、拖动，单击摸头、双击打开小窝，右键可投喂、休息、专注、设置及退出。
- 小窝：聊聊天、小书包、小钥匙、文件整理四页。气泡聊天、狐狸头像、手账插画、资料拖入、明确删除确认。
- VS Code：安装VSIX或使用已安装本机版。Ctrl+Shift+P执行「fox：打开陪伴小屋」。选中代码右键解析/建议；Ctrl+Alt+M解析；结果保留学习终端输出。扩展支持Markdown/TXT知识库，桌面另支持PDF/DOCX和文件夹。

## AI设置

桌面在「小钥匙」配置；VS Code执行「fox：配置AI接口、模型和密钥」。预设Agnes、DeepSeek、OpenAI、Claude、Gemini兼容接口、通义千问、Kimi和本机模型，也可自定义。
支持Chat Completions、Responses、Messages三种协议。Agnes预设agnes-3.0-flash、agnes-2.5-pro-beta、agnes-3.0-pro（用户文档标为即将上线）。所有模型ID可自由修改。认证方式支持自动、Bearer和x-api-key。配置保存不会发测试请求。

VS Code密钥保存在SecretStorage，桌面密钥用Windows DPAPI用户加密。两端分别配置。仅手动发送、解析或建议才调用AI；打开、切换、保存文件和日常互动不会自动调用。未将聊天中曾提供的密钥放进代码或测试。

## 资料与文件

导入资料保存本机副本。桌面支持TXT/MD/常见源码/PDF文字/DOCX段落与表格；每篇5MB、每批最多200篇、文件夹最多检查1000项。扫描PDF暂无OCR。
导入和搜索离线。附带资料默认关闭；开启后最多3段片段随问题发送。代码解析启用知识库辅助时也会发送匹配片段。
资料副本位于%APPDATA%/fox-code-meow/knowledge-desktop。桌面与VS Code的知识库分别保存。
「文件整理」可删除知识库副本，也有独立原文件删除。原文件删除不进回收站，需核对完整路径并输入DELETE；强制模式只解除只读，不提权、不结束进程，拒绝系统目录与链接。遇到占用等错误可能部分删除，按错误检查目标。

## 开发和验证

Python3.11+、Node.js、Windows。安装desktop/requirements.txt后运行：

```powershell
npm test
python test/assistant-check.py
python test/protocols-check.py
python test/desktop-check.py
python test/file-actions-check.py
python test/qt-check.py
python test/qt-assistant-check.py
python test/qt-flow-check.py
python test/run-host.py
```

Windows构建运行build.ps1；先生成独立EXE，再打包VSIX。源码不包含个人密钥、用户资料或本地测试profile。依赖许可证见third_party_licenses，接入依据见API_SOURCES.md。图像来自内置imagegen，原始方案与生成说明在design/。

界面徽章仅表示配置已保存，不冒充联网成功。桌宠生命感来自动画和本地交互，软件没有真实意识。不会自动执行代码或应用AI建议。

0.7.1修复Windows打包时误带PDF工具ICU DLL导致的QtWidgets加载失败。请使用此版本替代0.7.0；无需修改系统环境或自行下载DLL。构建后可运行python test/frozen-check.py直接验证EXE。
