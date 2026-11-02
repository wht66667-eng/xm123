# 接入依据与范围

Agnes：用户于本轮提供的Agnes 3.0 Flash、2.5 Pro Beta和3.0 Pro文档。Base URL https://apihub.agnes-ai.com/v1，支持chat/completions、responses、messages；Messages示例使用x-api-key和anthropic-version: 2023-06-01。3.0 Pro文档标为即将上线，不将格式示例作为可用证明。价格和额度不硬编码到界面。

核对官方文档（2026-11-02）：
- OpenAI模型：https://developers.openai.com/api/docs/models
- Responses：https://developers.openai.com/api/reference/responses/overview
- Claude模型：https://platform.claude.com/docs/en/models/overview
- Claude Messages：https://platform.claude.com/docs/en/api/messages/create
- DeepSeek：https://api-docs.deepseek.com/quick_start/pricing/
- Gemini兼容接口：https://ai.google.dev/gemini-api/docs/openai
- 千问兼容接口：https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope
- Kimi入口：https://platform.kimi.com/docs/get-api-key

实现文本聊天与代码解释；三协议均有本机HTTP模拟验证。没有声称验证真实云端账户，也不执行模型发出的工具调用。图像URL、多模态和超长上下文不因服务商支持就自动成为本插件的已实现功能。所有预设模型都可手动改ID；账户权限和服务可用性由服务商决定。
