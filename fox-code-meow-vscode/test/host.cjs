'use strict';
const vscode = require('vscode');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');

exports.run = async function () {
  const extension = vscode.extensions.getExtension('fox-local.fox-code-meow');
  assert.ok(extension, 'Extension is discoverable in the real host');
  await extension.activate();
  assert.equal(extension.isActive, true);
  const commands = await vscode.commands.getCommands(true);
  for (const id of ['openHome','openPet','chat','openTerminal','openPanel','explainSelection','suggestSelection','configureAI','searchKnowledge','importKnowledge','stop','export']) assert.ok(commands.includes('foxMeow.' + id), id);
  const requests=[];
  const server=http.createServer((req,res)=>{let body='';req.on('data',d=>body+=d);req.on('end',()=>{requests.push(JSON.parse(body));res.writeHead(200,{'Content-Type':'text/event-stream'});res.end('data: {"choices":[{"delta":{"content":"喵，这一行把结果返回给调用者。"},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n');});});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  try {
    const config=vscode.workspace.getConfiguration('foxMeow');
    await config.update('apiBase',`http://127.0.0.1:${server.address().port}/v1`,vscode.ConfigurationTarget.Global);
    await config.update('model','local-test-model',vscode.ConfigurationTarget.Global);
    await vscode.commands.executeCommand('foxMeow.openHome');
    await vscode.commands.executeCommand('foxMeow.openTerminal');
    assert.equal(requests.length,0);
    assert.ok(vscode.window.terminals.some(t=>t.name==='fox 喵喵代码老师'));
    const doc=await vscode.workspace.openTextDocument({language:'python',content:'return x'});
    const editor=await vscode.window.showTextDocument(doc);editor.selection=new vscode.Selection(0,0,0,8);
    await vscode.commands.executeCommand('foxMeow.explainSelection');assert.equal(requests.length,1);
    assert.ok(requests[0].messages[1].content.includes('return x'));
    await vscode.commands.executeCommand('foxMeow.suggestSelection');assert.equal(requests.length,2);
    assert.ok(requests[1].messages[0].content.includes('代码改进建议'));
    if (process.env.FOX_HOST_TEST_RESULT) fs.writeFileSync(process.env.FOX_HOST_TEST_RESULT, JSON.stringify({ active:true, commands:true, realTerminal:true, localMockRequests:2, realAiCalled:false }), 'utf8');
  } finally {await new Promise(resolve=>server.close(resolve));}
};
