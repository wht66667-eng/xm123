# fox 安全学习 · 手机端项目

## Android APK

`fox-safety-1.0.0.apk` 为已签名 Android 安装包，要求 Android 8.0 或更高版本。内置 2000 条双源题库，可离线检索；顶部可复制 fox 页面脚本。学校与实训功能仍需连接 Python 后端。

点击「连接服务」可设置地址，默认填入用户指定的 `https://jouxyfwglzx.cn`。该服务器尚未部署成功：当前 SSH 密钥被拒绝，域名预填不代表后端已上线。

重新打包运行 `python android/build.py`，依赖本机 Android SDK 36 build-tools / android-35 platform 与 JDK 17。签名证书 CN=fox；签名私钥保存在用户配置目录，不包含在交付包中。已通过 APK v2/v3 签名校验，并在 Android 模拟器安装启动、验证内置题库加载。

手机网页界面 + Python Flask 服务。整合 Scwizard 的学校平台 API/SQLite 题库与用户提供的 answer.js 页面题库，移动端签名为 fox。

## 启动

需要 Python 3.11 或更高版本。在项目目录执行：

```powershell
python -m pip install -r requirements.txt
python server.py
```

电脑打开 http://127.0.0.1:5080 。手机与电脑连接同一 Wi-Fi，打开 `http://电脑局域网IP:5080`。用 `ipconfig` 查看电脑 IPv4 地址。Windows 防火墙需要允许 Python 在专用网络接入。浏览器无法运行 Windows EXE，本项目不是 APK。

上线时使用可信的 HTTPS 反向代理与生产 WSGI 服务；不要把 Flask 开发服务直接暴露到公网。登录密码仅在本次请求中使用；会话与平台 token 存放于服务器内存，重启即失效。不要在不可信网络通过明文 HTTP 输入真实密码。

## 功能

- 双来源题库检索，明确区分选项字母和平台选项 ID。
- 学校查找、验证码刷新、登录、任务列表、考试/练习模式。
- 获取试卷、按题库填写、逐题保存、停止、练习翻页、手动交卷。
- 从练习接口返回的正确选项补充本地题库；未匹配题目停止自动填写。
- fox 页面适配脚本下载/复制，包含开始、停止、进度面板，最终交卷由用户完成。

学校平台依赖实时接口与本人账号；本地验证不代表平台允许、接受或计分成功。没有真实账号时无法验证登录后端到端流程。原项目中“期望分数/故意答错”未移植，当前按已匹配题库填写，答案需自行核对。

## 页面脚本

下载 `/adapter.js`，在支持用户脚本的手机浏览器里导入。将头部 `@match https://example.invalid/*` 改成实际答题页面域名。脚本只在手动点击开始后运行，沿用原脚本 `.type` / `.content` / `.option` / `.next.btn` 的结构。网站改版时需要更新选择器。普通手机网页不能跨站操作答题页；iOS/Safari 等须自行选择支持用户脚本的扩展环境，本项目没有验证具体手机浏览器兼容性。

## 来源与限制

- `upstream/`：https://github.com/Scwizard/jiangsu-safety-competition/ ，保留 Apache-2.0 LICENSE 与作者署名。离线副本含原项目完整源码及题库。
- `answer.js`：https://temp.ordylan.com/answer.js ，保留原文件，未执行远程代码；页面适配器内嵌其题库。该文件未附明确许可证，公开分发前需确认原作者授权。
- 用户提供的 EXE 已提取 PyInstaller 归档目录和 Python 代码常量进行静态分析，未执行。它连接另一套 `xg.jszjztc.com` 实训平台。`xg.py` 独立重建 GBK 表单桥接，提供登录、学习翻页、考试表单、成绩与证书导航/PDF 响应。自动爬取完整题库、重复题消歧和一键考试尚未移植，不能声称 EXE 已完整移植。详见 `exe-analysis.txt` 与 `exe-inventory.txt`。
- `fox` 是移动界面与适配署名，不替代原作者署名。

## 验证

运行 `python verify.py` 验证本地题库、接口边界、模拟平台登录/试卷/答题链路。所有平台写操作在测试中模拟，不会向真实平台交卷。
