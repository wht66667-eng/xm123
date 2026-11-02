'use strict';
const {test}=require('node:test');const assert=require('node:assert/strict');const http=require('node:http');const api=require('../src/api.cjs');
for(const protocol of ['chat','responses','messages'])test('manual '+protocol+' request uses matching wire schema and streaming parser',async()=>{
 const calls=[];const server=http.createServer((req,res)=>{let raw='';req.on('data',d=>raw+=d);req.on('end',()=>{calls.push({url:req.url,headers:req.headers,body:JSON.parse(raw)});res.writeHead(200,{'Content-Type':'text/event-stream'});const events=protocol==='responses'?[{type:'response.output_text.delta',delta:'协议回答'},{type:'response.completed',response:{usage:{total_tokens:8}}}]:protocol==='messages'?[{type:'content_block_delta',delta:{type:'text_delta',text:'协议回答'}},{type:'message_delta',delta:{stop_reason:'end_turn'}}]:[{choices:[{delta:{content:'协议回答'},finish_reason:'stop'}]}];res.end(events.map(e=>'data: '+JSON.stringify(e)+'\n\n').join(''));});});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 try{
  assert.equal(calls.length,0);let answer='';const result=await api.explain({key:'local-test-key',endpoint:`http://127.0.0.1:${server.address().port}/v1`,protocol,model:'test-model',messages:[{role:'system',content:'规则'},{role:'user',content:'问题'}],onText:t=>answer+=t});
  assert.equal(answer,'协议回答');assert.equal(result.finishReason,'stop');assert.equal(calls.length,1);const c=calls[0];assert.equal(c.url,'/v1/'+({chat:'chat/completions',responses:'responses',messages:'messages'})[protocol]);
  if(protocol==='responses'){assert.ok(c.body.input);assert.equal(c.body.store,false);assert.equal(c.body.messages,undefined);}else if(protocol==='messages'){assert.equal(c.body.system,'规则');assert.equal(c.body.messages.length,1);assert.equal(c.headers['x-api-key'],'local-test-key');assert.equal(c.headers.authorization,undefined);}else{assert.equal(c.body.messages.length,2);assert.equal(c.headers.authorization,'Bearer local-test-key');}
 }finally{await new Promise(r=>server.close(r));}
});
test('protocol URL replacement never appends another endpoint',()=>{
 assert.equal(api.resolveEndpoint('https://example.test/v1/chat/completions','responses').url,'https://example.test/v1/responses');
 assert.equal(api.resolveEndpoint('https://example.test/v1/messages').protocol,'messages');
 assert.equal(api.resolveEndpoint('https://example.test/v1/responses').url,'https://example.test/v1/responses');
});
