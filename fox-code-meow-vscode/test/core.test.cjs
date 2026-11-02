'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const core = require('../src/core.cjs');
const { explain, ENDPOINT } = require('../src/api.cjs');

test('secret files are blocked and source code remains eligible', () => {
  for (const f of ['C:\\work\\.env','/x/.env.local','/x/key.pem','/x/.ssh/id_ed25519']) assert.equal(core.isSensitiveFile(f), true);
  for (const f of ['/x/src/main.py','/x/env.js']) assert.equal(core.isSensitiveFile(f), false);
});
test('redaction keeps line numbers and does not upload literal keys', () => {
  const source = 'api_key = "sk-unit-test-not-real-key-123456789"\npassword: "not-a-real-password"\nprint("hello")';
  const r = core.redact(source);
  assert.ok(!r.text.includes('sk-unit-test')); assert.ok(!r.text.includes('not-a-real-password'));
  assert.equal(r.text.split('\n').length, 3); assert.ok(r.count >= 2);
});
test('chunks retain every source line and reject oversized single line', () => {
  const text = Array.from({length: 201}, (_,i) => 'line '+i).join('\n');
  const chunks = core.chunksOf(text, 7, 80);
  assert.equal(chunks.length, 3); assert.equal(chunks[1].firstLine, 87);
  assert.equal(chunks.at(-1).lastLine, 207);
  assert.equal(chunks.map(x => x.text).join('\n'), text);
  assert.throws(() => core.chunksOf('x'.repeat(10001), 1));
});
test('prompt contains real line numbers, chosen style and source trust boundary', () => {
  const m = core.makeMessages({code:'return x',filename:'work/main.py',language:'python',firstLine:42,lastLine:42,tone:'温柔猫娘',level:'零基础',mode:'line'});
  assert.match(m[0].content,/猫娘/); assert.match(m[0].content,/逐行/);
  assert.match(m[1].content,/42 \| return x/); assert.match(m[1].content,/BEGIN_SOURCE_/);
  assert.ok(!m[1].content.includes('work/'));
});
test('SSE parser handles fragmented and CRLF events', () => {
  const events=[];const parser=new core.SSEParser(x=>events.push(x));
  parser.feed(': ping\n\ndata: {"choices":[{"delta":{"content":"喵"}}]}\r');
  parser.feed('\n\r\ndata: {"choices":[],"usage":{"total_tokens":4}}\n\ndata: [DONE]\n\n');
  parser.end();assert.equal(events.length,2);assert.equal(events[0].choices[0].delta.content,'喵');
});

function mockTransport(chunks, status=200) {
  const state={calls:0,body:'',url:''};
  state.request=(url, options, callback)=>{
    state.calls++;state.url=url;
    const req=new EventEmitter();
    req.end=body=>{state.body=body;setImmediate(()=>{const res=new EventEmitter();res.statusCode=status;res.resume=()=>{};callback(res);for(const part of chunks)res.emit('data',Buffer.from(part));res.emit('end');});};
    req.destroy=()=>{};
    return req;
  };
  return state;
}
test('API uses only official endpoint and parses text, usage and completion', async()=>{
  const t=mockTransport(['data: {"choices":[{"delta":{"content":"讲解"},"finish_reason":null}]}\n\n','data: {"choices":[{"delta":{},"finish_reason":"stop"}],"usage":{"total_tokens":12}}\n\ndata: [DONE]\n\n']);
  let output='';const result=await explain({key:'dummy-key',model:'deepseek-flash',messages:[],onText:x=>output+=x},t);
  assert.equal(t.url,ENDPOINT);assert.equal(t.calls,1);assert.equal(output,'讲解');assert.equal(result.usage.total_tokens,12);
  assert.equal(JSON.parse(t.body).thinking.type,'disabled');
});
test('HTTP failure is surfaced and never retried', async()=>{
  const t=mockTransport([],401);
  await assert.rejects(explain({key:'dummy',model:'deepseek-flash',messages:[],onText:()=>{}},t),/API Key/);
  assert.equal(t.calls,1);
});
test('cancel before sending makes no request', async()=>{
  const t=mockTransport([]);const c=new AbortController();c.abort();
  await assert.rejects(explain({key:'dummy',model:'deepseek-flash',messages:[],signal:c.signal,onText:()=>{}},t),/取消/);
  assert.equal(t.calls,0);
});
test('incomplete stream is not reported as successful', async()=>{
  const t=mockTransport(['data: {"choices":[{"delta":{"content":"部分内容"}}]}\n\n']);
  await assert.rejects(explain({key:'dummy',model:'deepseek-flash',messages:[],onText:()=>{}},t),/完成前断开/);
});
