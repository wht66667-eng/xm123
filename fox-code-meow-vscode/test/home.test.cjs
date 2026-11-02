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
