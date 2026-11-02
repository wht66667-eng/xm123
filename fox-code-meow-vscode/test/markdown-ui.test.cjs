const{test}=require('node:test');const assert=require('node:assert/strict');const{renderMarkdown}=require('../src/markdown-ui.js');
class Node{constructor(tag,value=''){this.tag=tag;this.value=value;this.children=[];}appendChild(n){this.children.push(n);}replaceChildren(){this.children=[];}set textContent(t){this.value=t;this.children=[];}get textContent(){return this.value+this.children.map(n=>n.textContent).join('');}}
test('reply Markdown formats prose, preserves code symbols and treats HTML as text',()=>{
 const doc={createElement:t=>new Node(t),createTextNode:t=>new Node('#text',t)};const root=new Node('div');renderMarkdown(root,'# 标题\n\n**重点**\n\n- 一项\n\n```python\n# 注释\nx *= 2\n```\n<img src=x onerror=bad>',doc);
 assert.equal(root.children[0].tag,'h2');assert.equal(root.children[1].children[1].tag,'strong');assert.ok(root.textContent.includes('# 注释\nx *= 2'));assert.ok(root.textContent.includes('<img src=x onerror=bad>'));assert.ok(!root.textContent.includes('**重点**'));
});
