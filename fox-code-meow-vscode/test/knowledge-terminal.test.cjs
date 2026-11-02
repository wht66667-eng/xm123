'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const os=require('node:os');
const path=require('node:path');
const kb=require('../src/knowledge.cjs');
const {plainTerminal}=require('../src/terminal.cjs');
const api=require('../src/api.cjs');

test('knowledge can be imported, reloaded and retrieved without an external model',async()=>{
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'fox-kb-'));
  try {
    await kb.importDocument(root,'functions.md','# Python函数返回值\nreturn将函数结果返回给调用者。\n\n# 网络请求\nHTTP接口需要超时。');
    await kb.importDocument(root,'css.txt','# CSS颜色\n颜色控制页面样式。');
    const documents=await kb.loadDocuments([{dir:root,label:'我的知识库'}]);assert.equal(documents.length,2);
    const hits=kb.search(documents,'Python return 函数返回值');assert.match(hits[0].title,/返回值/);
    assert.match(kb.contextText(hits),/我的知识库/);assert.ok(kb.contextText(hits,20).length<=20);
    await assert.rejects(kb.importDocument(root,'x.exe','binary'),/Markdown/);
  } finally {await fs.rm(root,{recursive:true,force:true});}
});
test('terminal strips model-supplied escape codes and standardizes newlines',()=>{
  const output=plainTerminal('文本\x1b[2J\x1b]52;c;bad\x07\n下一行');
  assert.ok(!output.includes('\x1b'));assert.ok(!output.includes('\x07'));assert.match(output,/\r\n下一行/);
});
test('endpoint resolver accepts compatible APIs but disallows credential-bearing and remote HTTP URLs',()=>{
  assert.equal(api.resolveEndpoint('https://ai.example/v1/').url,'https://ai.example/v1/chat/completions');
  assert.equal(api.resolveEndpoint('https://api.deepseek.com/chat/completions').deepseek,true);
  assert.equal(api.resolveEndpoint('http://127.0.0.1:11434/v1').local,true);
  for(const value of ['http://remote.example/v1','https://user:pass@ai.example/v1','https://ai.example/v1?api_key=hidden','file:///etc/passwd'])assert.throws(()=>api.resolveEndpoint(value));
  assert.notEqual(api.secretName(api.resolveEndpoint('https://ai.example/v1')),api.secretName(api.resolveEndpoint('https://other.example/v1')));
});
