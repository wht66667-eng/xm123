'use strict';
const https = require('node:https');
const http = require('node:http');
const crypto = require('node:crypto');
const { SSEParser, friendlyError } = require('./core.cjs');
const ENDPOINT = 'https://api.deepseek.com/chat/completions';

function resolveEndpoint(base = ENDPOINT) {
  let u;
  try { u = new URL(base); } catch (_) { throw Error('AI接口地址不是有效网址。'); }
  const local = ['localhost', '127.0.0.1', '[::1]'].includes(u.hostname);
  if (u.username || u.password || u.search || u.hash) throw Error('接口地址不能包含账号、密码、查询参数或锚点。');
  if (u.protocol !== 'https:' && !(u.protocol === 'http:' && local)) throw Error('远程AI接口必须使用HTTPS；HTTP仅允许本机localhost/127.0.0.1。');
  u.pathname = u.pathname.replace(/\/+$/, '');
  if (!u.pathname.endsWith('/chat/completions')) u.pathname += '/chat/completions';
  return { url: u.toString(), origin: u.origin, local, deepseek: u.origin === 'https://api.deepseek.com' };
}

function secretName(endpoint) {
  return 'foxMeow.ai.' + crypto.createHash('sha256').update(endpoint.url).digest('hex').slice(0, 24);
}

function explain({ key, endpoint = ENDPOINT, model, messages, timeoutSeconds = 120, signal, onText }, transport) {
  const target = resolveEndpoint(endpoint);
  transport ||= target.url.startsWith('https:') ? https : http;
  return new Promise((resolve, reject) => {
    let settled = false; let finishReason = ''; let usage = null; let output = false;
    const end = (error, value) => { if (settled) return; settled = true; clearTimeout(timer); error ? reject(error) : resolve(value); };
    const body = JSON.stringify({ model, messages, stream: true, temperature: 0.2, max_tokens: 4096,
      ...(target.deepseek ? { thinking: { type: 'disabled' }, stream_options: { include_usage: true } } : {}) });
    let timer;
    if (signal?.aborted) { const e = new Error('解析已取消'); e.name = 'AbortError'; reject(e); return; }
    const req = transport.request(target.url, { method: 'POST', signal, headers: { 'Content-Type': 'application/json', ...(key ? { Authorization: `Bearer ${key}` } : {}), 'Content-Length': Buffer.byteLength(body) } }, res => {
      if (res.statusCode !== 200) { res.resume(); end(new Error(friendlyError(res.statusCode))); return; }
      const decoder = new TextDecoder();
      const parser = new SSEParser(event => {
        if (event.error) throw Error('服务返回了流式错误，解析已停止。');
        const choice = event.choices?.[0];
        if (choice?.delta?.content) { output = true; onText(choice.delta.content); }
        if (choice?.finish_reason) finishReason = choice.finish_reason;
        if (event.usage) usage = event.usage;
      });
      res.on('data', chunk => {
        if (settled) return;
        try { parser.feed(decoder.decode(chunk, { stream: true })); }
        catch (_) { req.destroy(); end(new Error('无法读取模型输出，已停止且没有自动重试。')); }
      });
      res.on('end', () => {
        if (settled) return;
        try {
          parser.feed(decoder.decode()); parser.end();
          if (!output) throw Error('模型没有返回讲解内容。');
          if (!finishReason) throw Error('连接在模型完成前断开，已保留部分讲解；没有自动重试。');
          end(null, { finishReason, usage });
        } catch (error) { end(error); }
      });
      res.on('error', () => end(new Error('响应连接中断，已保留部分内容。')));
    });
    timer = setTimeout(() => { req.destroy(); end(new Error('解析请求超时，已停止且没有自动重试。')); }, timeoutSeconds * 1000);
    req.on('error', error => {
      if (signal?.aborted || error.name === 'AbortError') { const e = new Error('已停止解析；已处理的请求可能仍产生费用。'); e.name = 'AbortError'; end(e); }
      else end(new Error('无法连接所配置的AI接口，请检查地址、网络或 VS Code 的代理配置。'));
    });
    req.end(body);
  });
}
module.exports = { explain, ENDPOINT, resolveEndpoint, secretName };
