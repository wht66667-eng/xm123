# 平台项目目录与功能记录

来源：用户提供的源码/EXE及其GitHub项目静态分析。快照日期2026-11-01；版本和接口后续可能变化，实际操作前核对当前代码。以下是知识索引，不是在线客户端实现。


# Scwizard/jiangsu-safety-competition

分析快照：4b797158c1886d5c457eaf33a4afd1a4a0218fbd

这是江苏省大学生安全知识竞赛的 Python 命令行程序，连接 mars.mycourse.cn；不是校园安 全通、不是 WeBan，也不是学校自建 labexam。

入口 main.py：载入SQLite题库 → 请求学校列表 → 关键词/编号选择 → MD5大写形式处理密码 → 显示验证码图片 → 登录 → 获取学习活动 → 区分练习与考试 → 逐题保存 → 交卷。

utils.py：pwdEncrypt进行密码摘要；searchCollegeByName筛选学校；getCaptcha下载验证码；login提交tenantCode、username、encryptedPassword、captchaCode、timestamp。authHeaders/authCookies携带token。getActivities读取任务；preparePaper/startPaper/recordQuestion/submitPaper是考试接口；Practice后缀的函数和getNear用于练习与翻页。

dbProcess.py：ensureSchema建立tiku与tiku_detail及唯一索引；insert_data新增/更新题目ID对应的答案ID；request_data按题目ID查库；count_questions等统计题库。这里答案是平台选项ID，不是网页A/B字母。

main.py中的练习流程读取optionList内isCorrect标记补题库；考试流程将输入n当作前n道答对，其余构造不同答案，因此只有特定计分规则下才等同目标分数。缺题时原版会选择第一个选项，无法保证得分。main_login还无条件调用未携带token的getUserIndex，可能造成额外失败，并非登录成功的可靠依据。

学校选择原版存在无范围检查、重新输入能力弱等问题。会话请求并非统一Session；密码控制台明文输入；大多数请求没有超时。导入main.py会直接开始交互和网络流程，不能当作纯函数库安全导入。

许可证：Apache-2.0，原作者Scwizard。仅改署名不能移除原有版权。用户提供的ZIP是本项目的另一份输入；原ZIP已另按字节解包供对照。



# answer.js 页面脚本

源地址为用户提供的 https://temp.ordylan.com/answer.js ，本次分析的是之前下载的本地快照，不保证远端后来没有更新。

answers是题干到选项字母串的映射，包含1000个题干键。fetchQuestion是唯一主要流程：读取.type和.content → 去掉题号 → 按题干精确查表 → 根据单选/多选找到Element UI的label并点击 → 等待800毫秒 → 检查是否有已选状态 → 点击.next.btn → 最多等待5秒题干变化 → 继续下一题。

判断题沿用单选分支；多选将ABCD拆成字母数组。脚本不负责学校登录、验证码、VPN，也不调用学校账号密码接口。网页本身若对点击执行保存，则会发生对应网站的写操作；不能把DOM脚本当成离线检索。

问题：只按题干匹配，不核对选项内容，选项乱序时可能错；多选直接点击可能把已选的正确选项取消，也不会清除旧的错误选项；找不到答案后仍可能因旧选项已选中而继续下一题；末尾引用未声明的questions，可能抛ReferenceError；没有开始/停止面板或防重复运行保护。最终交卷由用户在原页面完成，原脚本没有自动交卷代码。

源码没有提供明确许可证，不能仅因可以下载就认为能改署名重新授权。当前fox的adapter.js是另一个派生文件，增加停止、匹配校验与面板，不能冒充该原文件。


# 江苏省第十五届大学生安全知识竞赛 v1.0.4 EXE

该EXE是Python 3.11/PyInstaller控制台程序，入口main。静态字符串表明连接mars.mycourse.cn，流程是学校关键词选择、账号密码、验证码、练习/考试、SQLite查题、逐题保存与交卷。与03的xg_exam不是同一套代码。

已提取main.pyc和完整main.dis.txt。comparison.json比较了它与本地GitHub源码的函数字节码：多个具名辅助函数完全一致，killCaptcha存在差异，整个模块不完全一致。因此只能说属于同类且部分函数相同，不能把GitHub的main.py直接标成这个EXE完整反编译源码。

原始注释、排版与完整源码没有无损恢复。需要看原程序执行指令时打开main.dis.txt；需要读相近源码时参考01目录，但注意快照差异。没有运行此EXE或进行真实账号测试。


# MapleSugarCake/NJUPT_LabLearning

分析快照：9e1de26c9bb03a006c8c21b4a13a407e623a030c

用户粘贴内容中给出的旧URL为MapleSugarCake/LabLearningAutoPass，当前GitHub跳转到NJUPT_LabLearning。这里以实际克隆的提交为准，版本2.1.2，Python>=3.13。

功能边界：课程学习与课程题目提交，不包含正式考试实现。

main.py只包装启动；labpass_cli/cli.py组织交互设置、网络环境、登录方式与最终结果；config.py校验1–4个课程线程；runner.py管理受限线程池和独立会话；progress.py负责课程和整体进度；models.py定义显示用事件；logging_utils.py建立脱敏日志；version.py读取版本。

njupt_auth/config.py定义南邮的SSO、VPN及内网资源地址。内网资源是10.22.192.38一组地址，VPN域名为vpn.njupt.edu.cn，不能直接替换为海洋大学账号使用。auth.py中的authenticate组织VPN/统一身份认证/CAS及资源token交换；check_access以权限接口验证资源会话；import_token提供校园网token登录。browser.py启用临时Edge会话供本人完成交互验证并交接资源会话；transport.py控制重定向、超时及只读请求重试；crypto.py处理协议加密；models.py保存认证结果与会话快照；redaction.py脱敏账号、密码、token、URL等敏感字段；errors.py定义认证异常。

njupt_safetylabpass/client.py的SafetyLabClient读取课程和题目、验证字段并进行业务请求。course.py中的run_course按顺序处理一门课程：检查时长 → 获取题目 → 逐题提交 → 上报视频进度 → 单次完成提交 → 回读完成状态。coordination.py用共享锁串行写入并管理全局取消，所以课程线程数大于1也不代表写操作无限并发。models.py定义Course/Question/结果与状态；exceptions.py区分登录失效、网络失败、提交结果不确定等错误。

课程进度使用完整的十秒递增序列，每个成功包之后有独立随机等待；这属于接口上报，不能解读为程序实际播放并理解视频。失败或认证失效会阻止后续写入；不能撤销已经发出的请求。强制重提交只针对首次列表快照，不会不断加入新任务。

tests目录覆盖认证、重定向、浏览器交接、日志脱敏、课程顺序、强制模式、发包与线程调度；tools目录用于检查发布包及EXE冒烟。当前仅静态阅读，未因看到测试文件就声称已经运行通过。原项目密码输入可见；本次设置不保存磁盘，token隐藏输入。

许可证MIT，原作者信息保留。



# determine123/sjtu-lab-safety-learning-assistant

分析快照：用户提供的文件快照

这是版本1.6.0的Chrome/Edge MV3扩展，不是Python客户端。完整专题说明在本目录“交大详细解析.md”。

manifest.json只将内容脚本自动注入lab.sjtu.edu.cn与cps.sjtu.edu.cn。popup.html/popup.js是设置窗口，保存模型接口、API Key、模型名、阈值，向活动页面发送RUN/STATUS消息。assistant-core.js实现答案规范化、题干清理、选项文本重映射、模型JSON解析、置信度显示及TXT格式化。

content.js：scan按可见radio/checkbox的name分组；findStem从选项前截取题干；lookup依次尝试结构化题库、历史/种子记录和相似题；solve在本地失败后请求AI；renderList构造结果侧栏；apply在用户逐题确认后修改选项并派发input/change；collectReviewAnswers识别结果页明确标注的标准答案；importReviewAnswers保存结构化学习记录；exportReview导出复习文本。没有自动登录、刷视频、自动翻页和交卷。

background.js代理OpenAI兼容接口与可选搜索请求；listModels拉取模型列表；buildMessages组装题干选项与资料；callOnce请求并校验答案；ask执行有限模型候选回退。API Key保存在chrome.storage.local，搜索与模型使用同一把Key，配置自定义搜索端点需注意接收方。接口是否存在不能仅凭默认字符串判断。

bank-data.js有1452条结构化题目；bank.js是附加种子记录。tools/build-bank.mjs将Markdown题干、选项、标准答案转成JS数据，按语义去重并剔除答案冲突组。

固定0.99等置信度不等于真实正确概率。停止不会中断已发出的模型fetch。宽松字母提取可能把英文说明识别为答案；传统DOM扫描不覆盖所有自定义题型和VPN改写域名。代码不能原样套用江苏海洋大学。

本次已运行core与bank两个纯本地测试并通过；没有调用模型或真实考试。MIT作者determine123。



# hangone/WeBan

分析快照：036dc7272ac8e1d876471bf2ceaa2bc57dfaf8bf

这是安全微伴/安全微课的Python客户端。当前代码版本3.11.1，运行要求是Python>=3.12,<3.13；版本号3.11.1不是Python版本要求。目标主站weiban.mycourse.cn，课程还涉及mcwk、moon、lyra等同服务体系。

main.py负责参数、环境变量、TOML配置、运行目录、更新检查、交互账号录入、日志与多账号调度。实际配置优先级要分用户账号设置与全局设置查看get_setting/cli_or_env；文档总体为命令行>环境变量>配置文件。save_interactive_account登录成功后把账号及密码写进config.toml，这不是加密保险库；不要把真实config文件放进公开仓库。

api.py是接口层。LoggingSession统一HTTP头、请求与debug日志；handle_response检查HTTP及业务响应。WeBanAPI负责学校列表与学校配置、验证码、登录、项目、课程、轨迹、完课和考试接口。encrypt按协议以固定密钥AES-ECB加密登录请求体；这不是本地安全存储机制。login成功后保存userId/token并更新请求头。

client.py是业务编排。WeBanClient.login先处理验证码再登录；只在验证码错误等指定情形重试，不应把循环上限解读为不断尝试错误密码。run_project_cycle将项目课程与考试串联；run_study遍历课程并处理页面结构、题目、时长及完课；run_exam按模式检查考试机会、历史成绩、题库匹配率、逐题记录并交卷。false/true/perfect/force分别涉及跳过、正常、追求满分及强制再次考试，不是任意目标分数控分功能。

client.py前部大量页面/脚本解析辅助函数用于推断课件类型、页数、页面跳转、视频与答题轨迹；这些是课程协议适配，不是通用视频播放器。题库JSON加载与合并有本地和远程兜底，运行并非始终离线；AI功能也是可选外部服务。

captcha.py定义LoginCaptchaSolver和CaptchaHandler，以及图像掩码、候选匹配、浏览器探测等辅助函数。仓库实现了自动验证码识别和人工回退；本次只分析其职责，没有运行或替用户完成验证码。captcha_model.onnx是模型数据，不是可阅读的Python源文件。

config.example.toml是参数模板，requirements/pyproject/uv.lock定义依赖，Dockerfile和entrypoint.sh用于容器启动；.github工作流用于检查及跨平台构建。answer/answer.json是题库，不是账号库。

注意：直接运行main会处理学习/考试，不能把启动当成只读检测。debug日志可包含mycourse请求/响应，分享日志前需排查敏感内容。远程题库、更新检查和AI会引入外部请求。没有在真实平台运行，因此不保证当前接口可用。

许可证GPL-3.0。若分发其修改版本，需要遵循GPL条件，不能把整份派生程序直接改成fox的MIT；应与不同许可证项目明确区分。



# Scwizard/jiangsu-safety-platform-skip

分析快照：8c5d1b79f40a78ee05fcf05fd40ccdae6fad45d5

这是2026江苏省大学新生安全知识教育脚本，目标wap.xiaoyuananquantong.com/guns-vip-main，源码标识1.1.4-source。不是mars竞赛平台，也不是labexam。

main.py流程：创建共享Session → 选择江苏省学校 → 登录 → 读取必修课程及完成度 → 对未完成课件建立答题会话、查题库并提交 → 再查完成度 → 创建正式试卷 → 按题目文字查库并映射当前选项 → 等待后交卷 → 解析分数、补录错题 → 满分分支尝试下载证书 → 解绑openId → 上传统计。

utils.py：getAllSchools/getUserSchool查询并筛选学校；loginMethod提交collegeId/account/password并取userId。getArticles/getQuestions获取课件和题目；markArticleViewed上报状态；createUnitSession取提交凭证。getAnswerByQuestion规范化题干后从SQLite取答案文本列表；buildUnitAnswers按当前optionA–F文本反查对应字母；typeCode区分单选、多选、判断；saveWrongAnswers读取错题正确答案并更新database.db；creatExam/getExam/getExamId/imitateExam封装试卷与提交接口。

SQLite保存questionId、规范化question、answer(JSON字符串)和quesType。判断题用1/0，选择题保存正确选项文字，避免考试题ID和选项顺序变化时直接错用旧字母。旧getAnswerById仍引用database_new.db，当前主流程主要使用新的文本查库函数，不能把遗留函数当成当前入口。

代码存在文档不一致：README称改单线程，但main实际THREADS=0，线程池使用THREADS or len(unfinished)，有多个未完成课程时仍可能多线程。getUserSchool递归重试后没有return递归结果，可能把学校ID变成None；序号缺少边界检查。utils.end(code)有调用未给参数的分支，出错时可能再触发TypeError。

缺失答案时有默认A/判断默认值等回退，因此不能保证满分。课程多轮重试可能重复写入；共享Session跨线程使用也需审慎。密码input可见，登录地址使用HTTP；verify=False在这些HTTP请求上并不能提供加密保护，若换成HTTPS继续保留该参数则会取消证书验证。多个请求没有显式超时。

重要外部副作用：末尾会调用UntyingMethod解绑微信openId，不能把它仅看成普通退出登录。STATS默认True，upload_stats把score和runtime_ms发送到第三方IP的HTTP接口。源码声称不保存IP，不等于从客户端代码能证明服务器没有访问日志。本次未运行任何解绑、上报或答题请求。

一键安装并运行.bat不只是安装requests：还检测/下载Python、获取远程源码和自动启动。首次使用前应阅读，不能当成无副作用的文档。许可证Apache-2.0，作者Scwizard。



# wht66667-eng/xm123

分析快照：6fac7e7e55ad39ed9c388a4dda108599b74b5f7b

这是本对话中生成的派生整合项目，不是用户最初提供的完整第三方原源码。它组合了命令行源码、手机网页、Android容器、管理端和已有平台适配。

根main.py仍以竞赛平台流程为基础；score_plan.py将目标分数/单题分值转换为计划正确题数，预检全部选项和题库，再为其余题构造不同答案。只适用于等分值、错选/漏选零分等假设，不能保证服务端实际分数。school_select.py提供搜索、编号、重新搜索与确认；fox_config.py加载.env、检查参数、配置向导、环境检测；configure.py是配置入口，setup-environment.bat安装依赖。

mobile/server.py是Flask后端：学校列表、验证码、登录、题库搜索及受限平台动作；会话token留在进程内存。mobile/xg.py重建另一实训平台的GBK表单桥接，支持页面表单和导航及PDF响应；不是EXE全部功能的无损移植。mobile/admin.py在设置FOX_ADMIN_PASSWORD时启用管理登录、题库增删改查、导入导出和环境检测；未设置则禁用管理API。

mobile/web/app.js是学习端界面状态与答题操作；score-plan.js是前端控分计划；xg.js显示实训平台表单；admin.js配合admin.html提供管理工作台；adapter.js是从answer.js题库制作的用户脚本。HTML/CSS负责布局、品牌和移动适配，不自行认证学校账号。

mobile/android/src/.../MainActivity.java是原生Android Activity，使用WebView显示内置离线题库或指定后端，提供服务器设置、复制脚本和下载。它不是把Python嵌入手机，在线功能仍依赖服务器。android/build.py用SDK/JDK生成、对齐并签名APK；签名私钥在项目目录外，不包含在资料包中。deploy目录是systemd/nginx部署准备，并不代表阿里云已经上线。

test_score_plan.py、test_school_config.py及mobile中的test_admin.py/verify.py等是本地模拟测试；UI测试使用临时数据库或模拟页面。本对话曾验证这些局部流程，但没有因此完成学校真实账号、考试与云端部署验证。学校实验室labexam尚未完成适配。

主LICENSE用于fox新增代码MIT；上游Apache原代码和其他原作者内容见THIRD_PARTY_NOTICES，不能将所有外部内容视为fox独占。原版EXE字节未变；控制分电脑版为另一个派生构建。



## 实训安全EXE v1.0.0补充

用户提供文件的入口是xg_exam.py，PyInstaller/Python3.11。它连接xg.jszjztc.com，包含ASP.NET隐藏字段登录、练习题库、规范化索引、考试选项匹配、成绩复核、证书下载。不是JOU实验室平台。

静态提取出35个顶层函数；depyf生成22个函数文本，13个失败，其中包括main、crawl_bank、walk_and_answer和download_certificate。部分成功文本也有语义错误，不能当成完整可运行原源码。完整反汇编存在于用户的分析资料中；本skill不依赖该机器路径，不附可执行二进制或真实账号。

## 来源链接

- https://github.com/Scwizard/jiangsu-safety-competition/
- https://temp.ordylan.com/answer.js （未明确许可证，使用时核对）
- https://github.com/MapleSugarCake/NJUPT_LabLearning （旧名LabLearningAutoPass）
- https://github.com/determine123/sjtu-lab-safety-learning-assistant
- https://github.com/hangone/WeBan
- https://github.com/Scwizard/jiangsu-safety-platform-skip
- https://github.com/wht66667-eng/xm123
