'use strict';
const { test }=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');

function harness() {
  const commands=new Map();const store=new Map();const sent=[];const state={calls:0,requests:[],input:'sk-unit-test-not-real-123456789',terminalOutput:'',config:{},imports:[],documents:[]};
  const selection={isEmpty:false,start:{line:0,character:0},end:{line:0,character:8},active:{line:0,character:0}};
  const document={fileName:'C:/project/main.py',languageId:'python',version:1,uri:{toString:()=> 'file:///project/main.py'},lineCount:1,getText:()=> 'return x',lineAt:()=>({text:'return x'})};
  const context={subscriptions:[],extensionPath:path.join(__dirname,'..'),globalStorageUri:{fsPath:'C:/test-profile/fox'},secrets:{get:async k=>store.get(k),store:async(k,v)=>store.set(k,v),delete:async k=>store.delete(k)}};
  const panel={reveal:()=>{},webview:{html:'',onDidReceiveMessage:()=>{},postMessage:m=>sent.push(m)},onDidDispose:()=>{}};
  const vscode={
    commands:{registerCommand:(id,fn)=>{commands.set(id,fn);return {dispose(){}};},executeCommand:async(id,...args)=>commands.has(id)?commands.get(id)(...args):[]},
    workspace:{isTrusted:true,asRelativePath:()=> 'main.py',getConfiguration:()=>({get:(k,d)=>k in state.config?state.config[k]:d,update:async(k,v)=>{state.config[k]=v;}}),fs:{writeFile:async()=>{throw Error('Unexpected write');},stat:async()=>({size:100}),readFile:async()=>Buffer.from('password="private-test-value"')}},
    window:{activeTextEditor:{selection,document},showInputBox:async()=>state.inputs?.length?state.inputs.shift():state.input,showOpenDialog:async()=>state.files,showQuickPick:async items=>items[state.providerChoice||0],showInformationMessage:()=>{},showErrorMessage:m=>{state.error=m;},showWarningMessage:async()=> '开始分段解析',createStatusBarItem:()=>({show(){},dispose(){}}),createWebviewPanel:()=>panel,createTerminal:options=>{state.pty=options.pty;options.pty.onDidWrite(text=>{state.terminalOutput+=text;});options.pty.open();return {show(){},dispose(){options.pty.close();}};}},
    EventEmitter:class {constructor(){this.handlers=[];this.event=fn=>{this.handlers.push(fn);return {dispose(){}};};}fire(value){for(const fn of this.handlers)fn(value);}dispose(){this.handlers=[];}},
    ConfigurationTarget:{Global:1},
    ViewColumn:{Beside:2},StatusBarAlignment:{Right:2},env:{clipboard:{writeText:async()=>{}}},
    SymbolKind:{Function:11,Method:5,Constructor:8}
  };
  const sandbox={module:{exports:{}},exports:{},require:name=>{
    if(name==='vscode')return vscode;
    if(name==='./home.cjs')return require('../src/home.cjs');
    if(name==='./companion.cjs')return {publish:async()=>{},launch:async()=>{}};
    if(name==='./core.cjs')return require('../src/core.cjs');
    if(name==='./api.cjs')return {...require('../src/api.cjs'),explain:async o=>{state.calls++;state.requests.push(o);o.onText('这行把x返回给调用者喵。');return {finishReason:'stop',usage:{total_tokens:10}};}};
    if(name==='./knowledge.cjs')return {...require('../src/knowledge.cjs'),loadDocuments:async()=>state.documents,importDocument:async(root,file,text)=>{state.imports.push({root,file,text});}};
    if(name==='./terminal.cjs')return require('../src/terminal.cjs');
    return require(name);
  },AbortController,Buffer,setTimeout,clearTimeout,console};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../src/extension.cjs'),'utf8'),sandbox);
  sandbox.module.exports.activate(context);
  return {commands,store,state,sent,document,vscode,panel};
}

test('activation and opening panel send zero API requests',async()=>{
  const h=harness();assert.equal(h.state.calls,0);await h.commands.get('foxMeow.open')();assert.equal(h.state.calls,0);
  assert.match(h.state.terminalOutput,/不会执行 shell/);
});
test('setting a secret does not test or send it to a model',async()=>{
  const h=harness();await h.commands.get('foxMeow.setKey')();assert.equal(h.store.size,1);assert.equal(h.state.calls,0);
  await h.commands.get('foxMeow.deleteKey')();assert.equal(h.store.size,0);
});
test('only explicit explain command sends captured source',async()=>{
  const h=harness();await h.commands.get('foxMeow.explainSelection')();
  assert.equal(h.state.calls,1);assert.match(h.state.requests[0].messages[1].content,/return x/);
  assert.equal(h.document.getText(),'return x');assert.match(h.state.terminalOutput,/解开/);
  assert.match(h.state.terminalOutput,/这行把x返回/);
});
test('sensitive file blocks before requesting a key or API',async()=>{
  const h=harness();h.document.fileName='C:/project/.env';await h.commands.get('foxMeow.explainSelection')();
  assert.equal(h.state.calls,0);assert.equal(h.store.size,0);assert.match(h.state.error,/密钥/);
});
test('untrusted workspace cannot send code',async()=>{
  const h=harness();h.vscode.workspace.isTrusted=false;await h.commands.get('foxMeow.explainSelection')();
  assert.equal(h.state.calls,0);assert.match(h.state.error,/信任/);
});

test('AI configuration stores endpoint/model/key without sending a test request',async()=>{
  const h=harness();h.state.providerChoice=1;h.state.inputs=['https://ai.example/v1','custom-code-model','provider-test-key'];
  await h.commands.get('foxMeow.configureAI')();
  assert.equal(h.state.calls,0);assert.equal(h.state.config.model,'custom-code-model');assert.equal(h.state.config.apiBase,'https://ai.example/v1');assert.equal(h.store.size,1);
});
test('a different API never receives the old DeepSeek credential',async()=>{
  const h=harness();h.store.set('foxMeow.deepseek.apiKey','legacy-key-not-for-custom');h.state.input='custom-provider-test-key';h.state.config.apiBase='https://ai.example/v1';
  await h.commands.get('foxMeow.explainSelection')();
  assert.equal(h.state.calls,1);assert.equal(h.state.requests[0].key,'custom-provider-test-key');assert.equal(h.state.requests[0].endpoint,'https://ai.example/v1/chat/completions');
});
test('knowledge search and import are offline; imported text is sanitized',async()=>{
  const h=harness();h.state.input='函数返回值';h.state.documents=[{source:'我的知识库/test.md',text:'# 函数返回值\nreturn把结果返回给调用者。'}];
  await h.commands.get('foxMeow.searchKnowledge')();assert.equal(h.state.calls,0);assert.match(h.state.terminalOutput,/return/);
  h.state.files=[{fsPath:'C:/notes/my-note.md'}];await h.commands.get('foxMeow.importKnowledge')();
  assert.equal(h.state.imports.length,1);assert.ok(!h.state.imports[0].text.includes('private-test-value'));assert.equal(h.state.calls,0);
});
test('suggestion command sends suggestion task and local references to AI',async()=>{
  const h=harness();h.state.documents=[{source:'内置知识库/python.md',text:'# return返回值\n函数return x把结果返回。'}];
  await h.commands.get('foxMeow.suggestSelection')();assert.equal(h.state.calls,1);
  assert.match(h.state.requests[0].messages[0].content,/代码改进建议/);assert.match(h.state.requests[0].messages[1].content,/BEGIN_LOCAL_REFERENCE/);
  assert.match(h.state.terminalOutput,/代码建议小课堂/);
});

test('manual chat sends only typed question and no editor source',async()=>{
  const h=harness();h.state.config.apiBase='http://127.0.0.1:9999/v1';h.state.input='解释一下递归';
  assert.equal(h.state.calls,0);
  await h.commands.get('foxMeow.chat')();
  assert.equal(h.state.calls,1);
  assert.equal(h.state.requests[0].messages[1].content,'解释一下递归');
  assert.ok(!JSON.stringify(h.state.requests[0].messages).includes('return x'));
  assert.ok(h.state.terminalOutput.includes('fox'));
});

test('cancelled chat makes zero requests',async()=>{
  const h=harness();h.state.input=undefined;
  await h.commands.get('foxMeow.chat')();assert.equal(h.state.calls,0);
});

test('webview supplied chat text does not open another input dialog or attach editor code',async()=>{
 const h=harness();h.state.config.apiBase='http://127.0.0.1:9999/v1';
 const result=await h.commands.get('foxMeow.chat')('只发送这句话');assert.equal(h.state.calls,1);assert.equal(h.state.requests[0].messages[1].content,'只发送这句话');assert.ok(result.content);assert.ok(!JSON.stringify(h.state.requests[0].messages).includes('return x'));
});
