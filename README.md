# fox 安全学习 · 控分版

**fox 独家定制 · Copyright (c) 2026 fox · MIT License**

fox 新增代码采用 [MIT 许可证](LICENSE)。基于上游的原始代码仍按原许可证使用，原作者与第三方许可见 [第三方说明](THIRD_PARTY_NOTICES.md)，原 Apache-2.0 文本已独立归档。

## v1.1 学校选择与环境配置

电脑版沿用用户提供的 v1.0.4 命令行操作方式，启动菜单提供「开始运行 / 环境配置 / 环境检测」。学校可按关键词搜索、输入编号选择并确认；未找到可重新搜索，留空列出全部。密码输入不回显。

- **无需 Python 的电脑版**：[下载 fox-safety-desktop.exe](desktop/fox-safety-desktop.exe)。双击运行，选择 2 配置，选择 3 检测环境。
- **源码首次运行**：Windows 双击 `setup-environment.bat` 安装依赖并配置；也可执行 `python configure.py`。
- 配置包括默认学校关键词、答题间隔、请求超时、后端地址和端口、管理密码。环境变量优先于 `.env`，后端先使用 `mobile/.env`，不存在时读取仓库根目录 `.env`。
- EXE 配置保存在 EXE 同目录 `.env`，持久题库放在 `%LOCALAPPDATA%/fox/safety-learning`；不要将 `.env` 上传 GitHub。
- 手机端可留空关键词加载全部学校，登录前确认学校；管理端新增环境检测面板。
- 最新 APK：[fox-safety-1.1.0.apk](fox-safety-1.1.0.apk)。在线功能仍需部署后端。

默认后端只监听 `127.0.0.1`。局域网手机接入时在配置中将 `FOX_HOST` 改为 `0.0.0.0`；公网使用 HTTPS 反向代理。环境配置只是应用配置，不会自动安装 Python 或发布服务器。


PowerShell 中设置管理密码并启动后端：

```powershell
cd mobile
$env:FOX_ADMIN_PASSWORD = '请替换为你自己的长随机密码'
python -m pip install -r requirements.txt
python server.py
```

打开 `http://127.0.0.1:5080/admin`。未配置密码时管理 API 禁用；公网部署必须使用 HTTPS。不要将实际密码提交到 GitHub。每次更改题库前可先导出备份；管理员编辑会影响手机平台题库，不会修改已打包 EXE 内部的题库副本。

管理端测试：在 `mobile` 目录运行 `python -m unittest test_admin.py`。阿里云后端尚未部署，管理页面暂不能通过默认公网域名访问。

## 下载与手机使用

- 本仓库根目录 `fox-safety-1.1.0.apk`：Android 8.0 及以上，内置离线题库。
- 学校平台、实训和控分功能依赖后端。APK 点击「连接服务」填写服务器地址。
- 默认预填 `https://jouxyfwglzx.cn`；**该域名后端尚未部署成功**，不能把预填地址视为已上线。
- 后端及手机页面源码在 `mobile/`。进入该目录安装其 `requirements.txt` 后运行 `python server.py`，监听 5080 端口。
- 当前 APK 自身不包含 Python 后端，控分设置由连接后的手机网页提供。

## Python 命令行运行

安装 Python 3.11，确保已加入 PATH。在本仓库根目录运行：

```powershell
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
python main.py
```

按提示选择学校、输入账号密码与验证码、选择考试任务，然后输入目标分数、每题分值和每题间隔。练习模式沿用原项目逻辑。

## 控分规则

例如 100 道题，每题 1 分，目标 80 分，计划让 80 道题按题库作答，其余题提交与正确答案不同的有效选项。

- 仅支持等分值、全对得分且错选/漏选均不得分的试卷。部分给分、倒扣分和不等分值暂不支持。
- 目标分数必须是每题分值的整数倍，且在零分到满分范围内。
- 先验证整份试卷：缺少题库答案、选项失效或无法构造不同答案时停止，避免边答边猜。
- 平台已创建的试卷可能消耗考试次数，即使预检失败也应在原平台检查状态。
- 单题保存失败就停止，不自动交卷。命令行保存前输入 `YES`，完成后输入 `SUBMIT` 才交卷；手机端需手动交卷。
- 目标只是作答计划，平台判分与题库准确性决定实际成绩，不保证精确得分。

## 打包 Windows EXE

```powershell
python -m pip install pyinstaller
python -m PyInstaller --add-data "utils.py:." --add-data "database.db:." --add-data "dbProcess.py:." --add-data "donation.jpg:." --hidden-import score_plan --onefile --exclude-module pandas --exclude-module matplotlib --exclude-module IPython --exclude-module ipywidgets main.py
```

输出文件在 `dist/main.exe`。这条命令用于 Windows EXE，Android APK 构建请参阅 `mobile/android/build.py` 与移动端说明。

## 验证

```powershell
python -m unittest discover -p "test_score_plan.py"
```

已验证目标边界、小数分值、缺题、失效选项和多选题计划。真实平台账号、计分与交卷未实测；测试不会向真实平台提交试卷。

原项目题库与页面脚本来源信息见 `mobile/README.md`。请保留原作者权利声明，fox 署名不替代原作者署名。
