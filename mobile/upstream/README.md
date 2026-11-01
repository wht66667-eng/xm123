# fox 安全学习 · 控分版

基于 [Scwizard/jiangsu-safety-competition](https://github.com/Scwizard/jiangsu-safety-competition/) 改造，保留原作者署名与 Apache-2.0 许可证。移动适配、控分改造署名：**fox**。

## 下载与手机使用

- 本仓库根目录 `fox-safety-1.0.0.apk`：Android 8.0 及以上，内置离线题库。
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
