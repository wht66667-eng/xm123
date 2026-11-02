'use strict';
const {test}=require('node:test');const assert=require('node:assert/strict');
const home=require('../src/home.cjs');
test('home interactions persist locally and action routing is explicit',async()=>{
 let callback;const sent=[],commands=[],state=new Map();
 const panel={webview:{onDidReceiveMessage:f=>callback=f,postMessage:async m=>sent.push(m)}};
 const vscode={ViewColumn:{Beside:2},window:{createWebviewPanel:()=>panel},commands:{executeCommand:async c=>commands.push(c)}};
 const context={subscriptions:[],globalState:{get:(k,d)=>state.get(k)??d,update:async(k,v)=>state.set(k,v)}};
 home.open(vscode,context);await callback({action:'ready'});await callback({action:'pat'});await callback({action:'rest'});
 assert.equal(state.get('companion.pats'),1);assert.equal(commands.length,0);assert.ok(sent.some(m=>m.stats?.includes('1 次')));
 await callback({action:'chat'});assert.deepEqual(commands,['foxMeow.chat']);
 await callback({action:'unknown'});assert.equal(commands.length,1);
 assert.ok(panel.webview.html.includes("default-src 'none'"));
});

test('webview manual chat forwards only validated input and returns a reply bubble',async()=>{
 let callback;const sent=[],calls=[];
 const panel={webview:{onDidReceiveMessage:f=>callback=f,postMessage:async m=>sent.push(m)}};
 const vscode={ViewColumn:{Beside:2},window:{createWebviewPanel:()=>panel},commands:{executeCommand:async(...args)=>{calls.push(args);return {content:'本机模拟回答',complete:true};}}};
 const context={subscriptions:[],globalState:{get:(k,d)=>d,update:async()=>{}}};home.open(vscode,context);
 await callback({action:'ready'});assert.equal(calls.length,0);
 await callback({action:'chat',text:'解释一下递归'});assert.deepEqual(calls,[['foxMeow.chat','解释一下递归']]);assert.ok(sent.some(x=>x.chatDone&&x.content==='本机模拟回答'));
 await callback({action:'chat',text:'x'.repeat(6001)});assert.equal(calls.length,1);assert.ok(sent.some(x=>x.error));
});
