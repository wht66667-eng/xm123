'use strict';
const suffix={chat:'/chat/completions',responses:'/responses',messages:'/messages'};
function infer(path){return Object.keys(suffix).find(k=>path.endsWith(suffix[k]))||'chat';}
function requestSpec(protocol,messages,model,key,target,{stream=true,auth='auto',version='auto'}={}){
  const headers={};const authMode=auth==='auto'?(protocol==='messages'&&target.hostname!=='api.anthropic.com'?'x-api-key':'bearer'):auth;
  if(key)headers[authMode==='x-api-key'?'x-api-key':'Authorization']=authMode==='x-api-key'?key:'Bearer '+key;
  const system=messages.filter(m=>m.role==='system').map(m=>m.content).join('\n');const turns=messages.filter(m=>m.role!=='system');let body;
  if(protocol==='responses')body={model,input:messages,max_output_tokens:4096,stream,store:false};
  else if(protocol==='messages'){
    headers['anthropic-version']=version==='auto'?(target.hostname==='api.anthropic.com'?'2026-10-21':'2023-06-01'):version;
    body={model,system,messages:turns,max_tokens:4096,stream};
  }else body={model,messages,stream,...(target.hostname==='api.openai.com'?{max_completion_tokens:4096}:{max_tokens:4096,temperature:0.2}),...(target.origin==='https://api.deepseek.com'?{thinking:{type:'disabled'},...(stream?{stream_options:{include_usage:true}}:{})}:{})};
  return {headers,body};
}
function eventText(protocol,event,state){
  if(event.error||event.type==='error'||event.type==='response.failed')throw Error('模型服务返回错误');
  if(protocol==='responses'){
    if(event.type==='response.output_text.delta')return event.delta||'';
    if(event.type==='response.completed'){state.finishReason='stop';state.usage=event.response?.usage||null;}
    if(event.type==='response.incomplete')state.finishReason='length';
  }else if(protocol==='messages'){
    if(event.type==='content_block_delta'&&event.delta?.type==='text_delta')return event.delta.text||'';
    if(event.type==='message_delta'&&event.delta?.stop_reason)state.finishReason=['end_turn','stop_sequence'].includes(event.delta.stop_reason)?'stop':event.delta.stop_reason==='max_tokens'?'length':event.delta.stop_reason;
    if(event.usage)state.usage=event.usage;
  }else{
    const c=event.choices?.[0];if(c?.finish_reason)state.finishReason=c.finish_reason;if(event.usage)state.usage=event.usage;return c?.delta?.content||'';
  }
  return '';
}
function responseText(protocol,data){
 if(protocol==='responses')return data.output_text||(data.output||[]).flatMap(o=>o.content||[]).filter(c=>c.type==='output_text').map(c=>c.text||'').join('');
 if(protocol==='messages')return (data.content||[]).filter(c=>c.type==='text').map(c=>c.text||'').join('');
 return data.choices?.[0]?.message?.content||'';
}
module.exports={suffix,infer,requestSpec,eventText,responseText};
