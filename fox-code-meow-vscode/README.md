# fox 喵喵代码老师 0.2.0

本机专用 VS Code 中文代码学习插件，作者 fox，MIT。支持可爱猫娘讲解、代码建议、专用学习终端、本地知识库和自行填写 OpenAI 兼容 AI 接口。

## 先配置自己的 AI

按 Ctrl+Shift+P 搜索 **fox：配置AI接口、模型和密钥**。选择 DeepSeek 官方、自定义兼容接口或本机模型，再填写地址、模型 ID 和 API Key。密钥在隐藏框输入，保存到 VS Code SecretStorage，不写进项目或普通设置。配置本身不会发送测试请求。

- DeepSeek 地址：https://api.deepseek.com ，模型按账号支持情况填写，例如插件默认 deepseek-flash。
- 其他服务可填 https://服务商/v1 或完整 /chat/completions URL，需支持 OpenAI 兼容 Chat Completions 流式响应。
- 本机模型例如 http://127.0.0.1:11434/v1 ，模型应已安装；免认证服务可不填 Key。
- 远程地址须HTTPS，HTTP仅允许本机回环；不能夹带账号密码或查询参数。
- 不同接口的密钥分开保存，不把原DeepSeek密钥发到新服务。

此前聊天中出现的真实密钥未内置、未用于测试，建议更换后在隐藏框自行填写。

## 终端学习

选中代码，右键 **fox：中文解析选中代码** 或 Ctrl+Alt+M。默认在 **fox 喵喵代码老师** 终端流式显示讲解。右键 **fox：给选中代码提出建议** 可获取问题依据、改进方案和测试建议，不执行、不应用修改。

终端是学习界面，不是PowerShell，不会执行Shell命令。支持输入以下指令并回车：

| 指令 | 行为 |
|---|---|
| 帮助 | 看帮助，不调用AI |
| 解析 / 解析选区 | 讲解编辑器选中的代码 |
| 逐行 / 函数 / 文件 | 讲解相应范围 |
| 建议 | 给选中代码提出改进建议 |
| 停止 / Ctrl+C | 停止请求和后续分段 |
| 配置 | 打开接口配置窗口 |
| 知识库 关键词 | 纯本地资料检索，不调用AI |
| 导入 | 选择Markdown/TXT加入本地知识库 |
| 记住 | 将选中代码保存为知识卡片 |
| 导出 | 导出最近讲解或建议为Markdown |
| 清屏 | 清理学习终端显示 |

设置 foxMeow.outputMode 可切换终端、侧栏或两者；两者同时显示不会多发AI请求。函数定位依赖语言服务，不支持时手动选中。

## 本地知识库

内置Python/JavaScript、API、SQLite、异常处理、学习方法，以及之前安全教育项目的功能索引和题库格式知识。没有真实账号、密钥或自动考试程序。

使用 **fox：导入本地知识文档** 添加.md/.txt，或 **fox：把选中代码记入知识库**。脱敏副本保存在本机VS Code扩展globalStorage的knowledge文件夹，升级插件不覆盖个人资料。**fox：打开我的知识库文件夹** 可查看、编辑和备份。

单篇≤1MB、单次导入≤30篇、检索最多读取100篇。使用本地关键词和中文二元片段匹配，不调用联网Embedding。知识库是普通文本，不是密码保险箱；原导入文件不会修改。

默认 foxMeow.useKnowledgeBase 开启：手动解析时最多3段匹配片段（约3600字符）会随代码发送给当前AI，终端显示来源，不上传全部知识库。可关闭该设置，或只用“知识库 关键词”进行纯本地查询。资料只是参考，不保证适用当前项目。

## 可爱语气与手动触发

默认元气猫娘，可切换温柔猫娘或普通中文，以及零基础/有基础讲解。增加自然鼓励和可爱表达，技术解释与真实行号优先。

只有手动解析或建议命令会请求模型。打开、保存、切换文件、选中文本、打开终端、导入/搜索资料、设置密钥均不会自动请求。没有自动补全、后台遥测或静默重试。长内容分段前显示次数，默认每次操作最多12个请求。

停止不能撤回已发送代码或保证已处理部分不计费。默认拦截常见密钥文件、遮盖常见敏感赋值，不能替代人工检查。AI输出不等于执行验证。

“仅本机安装”不是“离线云AI”：点击后所选代码及匹配资料会发给你配置的服务。完全本地推理需另有可用的本机模型服务。

## 安装与验证

本机安装：code --install-extension fox-code-meow-0.2.0.vsix --force

若新命令未出现，执行 Developer: Reload Window（重新加载窗口）。卸载：code --uninstall-extension fox-local.fox-code-meow。个人知识文件和各接口密钥独立于扩展代码保存。

测试：npm test。21项本地测试通过；真实VS Code宿主已验证加载、专用终端、解析与建议，并以本机模拟API完成2次请求。没有调用真实云AI或用户真实密钥。

此插件只在本机安装，未发布到市场、GitHub或服务器。

## 0.3.0 陪伴版（开发记录）
新增 `fox：打开陪伴小屋`、`fox：召唤桌面宠物`、`fox：主动和伙伴聊聊天`。
桌面宠物支持拖动、摸摸、投喂、休息、专注计时、称呼记忆。右键可切换置顶、安静模式、减少动画、查看记录、最小化或退出。
聊天仅在输入并确认后联网，不附带编辑器源码。日常互动不联网。桌面通过本机 `%APPDATA%/fox-code-meow/learning.json` 接收讲解状态；不传递源码或密钥。个人陪伴数据保存在同目录 pet.json。插件小屋记录使用VS Code globalState。
桌面程序没有开机自启，也不监听网络端口。


## 从源码构建狐狸娘版

Node检查：`npm test`。桌面检查：`python test/desktop-check.py`。
先安装桌面构建依赖：`python -m pip install -r desktop/requirements.txt`。
PowerShell中构建：

```powershell
pyinstaller --noconfirm --onefile --windowed --name fox-pet --add-data "$PWD/assets;assets" --distpath desktop --workpath test-artifacts/pet-build --specpath test-artifacts desktop/pet.py
npx @vscode/vsce package --allow-missing-repository --no-dependencies
```

首次构建先生成EXE再打包VSIX。桌面源码使用Pillow加载动画，VS Code扩展无需额外运行时依赖。更新内容和后续优化见CHANGELOG.md。历史DELIVERY.md为0.3.0验收记录；当前版本以package.json和CHANGELOG为准。


## 桌面文档助手（0.5.0）
点击宠物下方「聊天 · 喂文件 · API设置」。API配置独立于VS Code，填入地址、模型、密钥后加密保存，不会发测试请求。导入和搜索离线。附带资料默认关闭，启用后最多3段匹配资料随问题发送。每次聊天只发送当前问题与选择的资料，无隐式历史上传。
支持PDF文本、DOCX段落/表格、TXT/MD及常见源码；单篇5MB、每批最多200篇，文件夹最多检查1000项。加密PDF或纯图片扫描件可能无可提取文本。文档副本在 `%APPDATA%/fox-code-meow/knowledge-desktop`。管理界面的永久删除只针对副本，电脑原文件保持不变。桌面密钥通过Windows DPAPI保护，不能跨Windows用户直接搬用。


### 原文件永久删除
桌面「删除原文件」独立于知识库副本管理。手动选择文件或文件夹，核对完整路径并输入DELETE后才执行，不进回收站。文件夹包含的内容一起永久删除。强制模式仅清除只读属性后重试，不提权、不终止占用进程；磁盘根、用户根、系统/应用目录及链接不支持删除。若操作中遇到占用或权限失败，目录可能已部分删除，应按错误检查目标。
