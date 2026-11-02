'use strict';
// Small safe DOM renderer: never interprets model text as HTML.
function renderMarkdown(root,value,doc=root.ownerDocument){
 root.replaceChildren();let paragraph=[],list=null,pre=null;
 function inline(node,text){const pieces=String(text).split(/(`[^`]+`|\*\*[^*]+\*\*|__[^_]+__|\*[^*\n]+\*)/g);for(const part of pieces){let tag=null,body=part;if(part.startsWith('`')&&part.endsWith('`')){tag='code';body=part.slice(1,-1);}else if((part.startsWith('**')&&part.endsWith('**'))||(part.startsWith('__')&&part.endsWith('__'))){tag='strong';body=part.slice(2,-2);}else if(part.startsWith('*')&&part.endsWith('*')){tag='em';body=part.slice(1,-1);}if(tag){const el=doc.createElement(tag);el.textContent=body;node.appendChild(el);}else node.appendChild(doc.createTextNode(part));}}
 function flush(){if(paragraph.length){const p=doc.createElement('p');inline(p,paragraph.join('\n'));root.appendChild(p);paragraph=[];}}
 for(const line of String(value).split('\n')){
  if(/^\s*```/.test(line)){flush();list=null;if(pre){pre=null;}else{const block=doc.createElement('pre');pre=doc.createElement('code');block.appendChild(pre);root.appendChild(block);}continue;}
  if(pre){pre.appendChild(doc.createTextNode(line+'\n'));continue;}
  const heading=line.match(/^(#{1,6})\s+(.+)$/);const item=line.match(/^\s*(?:[-*+]\s+|\d+[.)]\s+)(.+)$/);
  if(heading){flush();list=null;const h=doc.createElement('h'+Math.min(6,heading[1].length+1));inline(h,heading[2]);root.appendChild(h);}else if(item){flush();if(!list){list=doc.createElement('ul');root.appendChild(list);}const li=doc.createElement('li');inline(li,item[1]);list.appendChild(li);}else if(!line.trim()){flush();list=null;}else{list=null;paragraph.push(line);}
 }
 flush();
}
if(typeof module!=='undefined')module.exports={renderMarkdown};
