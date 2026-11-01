from pathlib import Path
import json
from server import bank

header = '''// ==UserScript==
// @name         fox 安全学习页面助手
// @namespace    fox.safety.mobile
// @version      1.0.0
// @description  手动开始、匹配填写、随时停止，最终手动提交
// @match        https://example.invalid/*
// @grant        none
// ==/UserScript==
// 题库来源：用户提供的 https://temp.ordylan.com/answer.js
// 移动适配与签名：fox；原题库作者权利保留。
(() => {
'use strict';
if (window.__foxAssistant) { window.__foxAssistant.show(); return; }
const answers = BANK;
let running=false, cancelled=false;
const host=document.createElement('div');
host.style.cssText='position:fixed;right:12px;bottom:24px;z-index:2147483647';
const root=host.attachShadow({mode:'open'});
root.innerHTML=`<style>:host{all:initial}section{width:250px;background:#173c32;color:white;border-radius:18px;padding:18px;font:14px/1.6 system-ui;box-shadow:0 6px 30px #0004}strong{font-size:24px;color:#ffab78}p{white-space:pre-wrap;overflow-wrap:anywhere}button{border:0;border-radius:8px;padding:12px;margin:3px;cursor:pointer;font:inherit;background:#f5f4ed;color:#173c32}button:disabled{opacity:.5}</style><section><strong>fox</strong> 页面助手<p role="status">准备就绪。请先打开答题页面。</p><button id="start">开始填写</button><button id="stop">停止</button><button id="hide">收起</button></section>`;
document.documentElement.append(host);
const status=root.querySelector('p'),start=root.querySelector('#start');
const show=()=>{root.querySelector('section').hidden=false;badge.hidden=true};
const badge=document.createElement('button');badge.textContent='fox';badge.hidden=true;badge.onclick=show;root.append(badge);
window.__foxAssistant={show};
root.querySelector('#hide').onclick=()=>{root.querySelector('section').hidden=true;badge.hidden=false};
root.querySelector('#stop').onclick=()=>{cancelled=true;status.textContent='已请求停止。请自行核对当前题目。'};
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const normalize=s=>s.replace(/^\\s*\\d+[、.．]/,'').replace(/\\s+/g,'').trim();
const lookup=new Map(Object.entries(answers).map(([q,a])=>[normalize(q),a]));
start.onclick=async()=>{
 if(running)return;running=true;cancelled=false;start.disabled=true;let count=0;
 try{
  while(!cancelled){
   const type=document.querySelector('.type'),content=document.querySelector('.content');
   if(!type||!content)throw Error('未找到题目。请确认当前页面与原脚本兼容。');
   const old=content.innerText,key=normalize(old),answer=lookup.get(key);
   if(!answer)throw Error('未匹配题库，已停止。请手动处理：'+old);
   const multi=type.innerText.replace(/\\s/g,'')==='多选题';
   const options=[...document.querySelectorAll('.option')];let matched=0;
   for(const option of options){
    if(cancelled)break;
    const label=option.querySelector(multi?'.el-checkbox__label':'.el-radio__label');
    const control=option.querySelector(multi?'.el-checkbox':'.el-radio');
    if(!label||!control)continue;
    const letter=label.innerText.trim().charAt(0),wanted=answer.includes(letter);
    const checked=!!control.querySelector('.is-checked, input:checked')||control.classList.contains('is-checked');
    if(wanted)matched++;
    if((multi&&wanted!==checked)||(!multi&&wanted&&!checked)){control.click();await delay(120)}
   }
   if(cancelled)break;
   if(matched!==answer.length)throw Error('题库答案与页面选项不一致，已停止。');
   await delay(800);
   const selected=options.filter(o=>o.querySelector('.el-radio__input.is-checked,.el-checkbox__input.is-checked,input:checked')).map(o=>o.querySelector(multi?'.el-checkbox__label':'.el-radio__label')?.innerText.trim().charAt(0)).sort().join('');
   if(selected!==answer.split('').sort().join(''))throw Error('页面没有正确选中答案，已停止。');
   count++;status.textContent='已填写 '+count+' 题。最后请自行核对并提交。';
   const next=document.querySelector('.next.btn');
   if(!next||next.disabled||next.classList.contains('is-disabled'))break;
   if(cancelled)break;next.click();
   const end=Date.now()+5000;let changed=false;
   while(Date.now()<end&&!cancelled){await delay(100);const current=document.querySelector('.content')?.innerText;if(current&&current!==old){changed=true;break}}
   if(cancelled)break;
   if(!changed){status.textContent+='\\n题目没有变化，已停止。若已到末题，请手动提交。';break}
  }
 }catch(e){status.textContent=e.message}finally{running=false;start.disabled=false}
};
})();
'''
Path('web/adapter.js').write_text(header.replace('BANK',json.dumps(bank,ensure_ascii=False)),encoding='utf-8')
