# 题库数据与共享适配

规范导出形状：`schema_version: 1, records: [...], conflicts: [...]`。每条记录至少含platform、id、stem、options、answer_kind、answer、sources。options元素保留id和text；answer是字符串数组；answer_kind只允许letters、ids、texts、boolean。记录不是“已验证正确”的保证。

| 来源 | 原始键与答案 | 转换要求 |
|---|---|---|
| answer.js | 题干→ABCD | letters，原文件没有选项文本，不承诺乱序安全 |
| SJTU | s/o/a/l | stem/options/letters；保留l来源标签 |
| mars SQLite | tiku.question是题目ID，answer为逗号分隔选项ID | ids；可从tiku_detail补题干与选项 |
| 江苏skip SQLite | 规范化题干，answer为JSON选项文本列表，quesType | texts；判断题3的1/0保留boolean；不能当成A/B |
| xg-lab | 账号JSON，题干、选项、参考答案与题型 | 先检查实际schema再写转换器，不能套用同名字段 |
| WeBan | answer.json | 先检视当前版本记录结构，再设计显式转换，不猜测 |

bank_tool仅实现已明确的前四种与canonical。不支持格式须说明并检查样本后扩展；不能声称工具已完成所有协议适配。

合并键：platform+id；没有ID则使用规范化题干与有序选项签名。不同平台从不自动合并。选项顺序不同的记录默认分别保留；要语义合并必须同时映射答案到选项文字。相同键有不同答案时把候选放conflicts，移出无冲突records，不投票掩盖差异。

实际匹配需按当前页面选项内容映射，而非直接沿用旧字母。ID答案先检查该ID仍在本卷；标准化应保留原题干，否定词与关键符号不应被过度清理。学习记录和官方结果页答案、AI建议、用户采用记录分别标来源；“采用过”不等于“官方正确”。

控分计划是独立于匹配的可选逻辑：等分值且全对得分/错选漏选零分时才可按目标分值计算正确题数；题库预检失败应明确停止计划。管理端修改题库前允许导出备份，导入事务化并校验重复项，不能把导入的JS当作可执行代码。
