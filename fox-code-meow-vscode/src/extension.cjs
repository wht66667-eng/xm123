'use strict';
const vscode = require('vscode');
const path = require('node:path');
const crypto = require('node:crypto');
const core = require('./core.cjs');
const companion = require('./companion.cjs');
const home = require('./home.cjs');
const api = require('./api.cjs');
const fs = require('node:fs/promises');
const knowledge = require('./knowledge.cjs');
const { LearningTerminal } = require('./terminal.cjs');

const SECRET = 'foxMeow.deepseek.apiKey';
let panel; let controller; let running = false; let last = null; let context; let terminal; let lastEditor;
let view = { code: '', notes: '', status: 'ฅ^•ﻌ•^ฅ 准备好啦！选一小段代码，我们一起把它读懂，喵～', meta: '仅手动触发 · 本地知识库 · 不修改源码' };

function targetEndpoint() { const cfg=vscode.workspace.getConfiguration('foxMeow');return api.resolveEndpoint(cfg.get('apiBase','https://api.deepseek.com'),cfg.get('protocol','auto')); }
function personalKnowledge() { return path.join(context.globalStorageUri.fsPath, 'knowledge'); }
function knowledgeRoots() { return [{ dir: path.join(context.extensionPath, 'knowledge'), label: '内置知识库' }, { dir: personalKnowledge(), label: '我的知识库' }]; }
async function localHits(query) { return knowledge.search(await knowledge.loadDocuments(knowledgeRoots()), query, 3); }

function openTerminal() {
  if (vscode.window.activeTextEditor) lastEditor = vscode.window.activeTextEditor;
  if (!terminal) terminal = new LearningTerminal(vscode, terminalCommand, stop);
  terminal.open(); return terminal;
}

async function terminalCommand(input) {
  const aliases = { '解析': 'foxMeow.explainSelection', '解析选区': 'foxMeow.explainSelection', '逐行': 'foxMeow.explainLine', '函数': 'foxMeow.explainFunction', '文件': 'foxMeow.explainFile', '建议': 'foxMeow.suggestSelection', '停止': 'foxMeow.stop', '配置': 'foxMeow.configureAI', '导入': 'foxMeow.importKnowledge', '记住': 'foxMeow.saveKnowledge', '导出': 'foxMeow.export' };
  if (aliases[input]) return vscode.commands.executeCommand(aliases[input]);
  if (input === '清屏') { terminal.clear(); return; }
  if (input.startsWith('知识库 ')) return searchKnowledge(input.slice(4).trim());
  terminal.line('喵～我听得懂：解析 / 逐行 / 函数 / 文件 / 建议 / 停止 / 配置 / 导入 / 记住 / 导出 / 清屏');
  terminal.line('查本地资料：知识库 关键词（只在本机搜索，不调用AI）。选好编辑器里的代码再用「解析」或「建议」哦。');
}

function safe(text) { return String(text).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]); }

function panelHTML(webview) {
  const nonce = crypto.randomBytes(18).toString('base64');
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'nonce-${nonce}'; script-src 'nonce-${nonce}';"><style nonce="${nonce}">
body{font:var(--vscode-font-size)/1.7 var(--vscode-font-family);padding:20px;color:var(--vscode-foreground);background:var(--vscode-editor-background)}header{display:flex;align-items:center;gap:12px;border-bottom:1px solid var(--vscode-panel-border);padding-bottom:14px}header strong{font-size:24px;color:#ec956d}header small{display:block;opacity:.65}h1{font-size:18px;margin:0}h2{font-size:14px;margin-top:24px}.bar{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0}button{font:inherit;padding:8px 12px;border:1px solid var(--vscode-button-border,transparent);border-radius:7px;background:var(--vscode-button-secondaryBackground);color:var(--vscode-button-secondaryForeground);cursor:pointer}button:hover{background:var(--vscode-button-secondaryHoverBackground)}button:focus-visible{outline:2px solid var(--vscode-focusBorder)}#stop{background:var(--vscode-button-background);color:var(--vscode-button-foreground)}#status{border-left:3px solid #ec956d;padding:8px 12px;background:var(--vscode-textBlockQuote-background);white-space:pre-wrap;overflow-wrap:anywhere}#meta{font-size:12px;opacity:.7;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}#code{font-family:var(--vscode-editor-font-family);font-size:12px;max-height:280px;overflow:auto;padding:12px;background:var(--vscode-textCodeBlock-background);border-radius:8px}#notes{user-select:text;line-height:1.9}footer{border-top:1px solid var(--vscode-panel-border);margin-top:30px;padding-top:15px;opacity:.65;font-size:11px}</style></head><body><header><strong>fox ฅ</strong><div><h1>喵喵代码老师</h1><small>ฅ 代码有点难？我们一起慢慢拆开它，喵～</small></div></header><div class="bar"><button data-action="api">配置AI接口</button><button data-action="key">设置密钥</button><button data-action="terminal">学习终端</button><button data-action="knowledge">查本地知识库</button><button data-action="settings">语气与显示</button><button id="stop" data-action="stop">停止</button><button data-action="export">导出笔记</button><button data-action="copy">复制笔记</button></div><p id="meta">${safe(view.meta)}</p><div id="status" role="status" aria-live="polite">${safe(view.status)}</div><h2>本次解析的代码</h2><pre id="code">${safe(view.code || '尚未选择代码。不会在打开、保存或切换文件时自动请求 API。')}</pre><h2>中文学习笔记</h2><pre id="notes">${safe(view.notes || '准备好就选中一小段代码，右键选择「fox：中文解析选中代码」喵。')}</pre><footer>Copyright © 2026 fox · MIT License<br>仅手动解析时发送代码及相关知识片段到你配置的AI接口；可随时停止，不执行代码、不自动修改文件。</footer><script nonce="${nonce}">const vscode=acquireVsCodeApi();document.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>vscode.postMessage({action:b.dataset.action}));window.addEventListener('message',e=>{const s=e.data;for(const id of ['code','notes','status','meta'])if(typeof s[id]==='string')document.getElementById(id).textContent=s[id]});</script></body></html>`;
}

function showPanel() {
  if (panel) { panel.reveal(vscode.ViewColumn.Beside, true); return; }
  panel = vscode.window.createWebviewPanel('foxMeow.learning', 'fox 喵喵代码老师', { viewColumn: vscode.ViewColumn.Beside, preserveFocus: true }, { enableScripts: true, retainContextWhenHidden: true, localResourceRoots: [] });
  panel.webview.html = panelHTML(panel.webview);
  panel.webview.onDidReceiveMessage(async message => {
    const routes = { stop: 'foxMeow.stop', key: 'foxMeow.setKey', api: 'foxMeow.configureAI', terminal: 'foxMeow.openTerminal', knowledge: 'foxMeow.searchKnowledge', settings: 'foxMeow.settings', export: 'foxMeow.export' };
    try {
      if (routes[message?.action]) await vscode.commands.executeCommand(routes[message.action]);
      else if (message?.action === 'copy' && view.notes) await vscode.env.clipboard.writeText(view.notes);
    } catch (e) { vscode.window.showErrorMessage(e.message || '操作未完成'); }
  }, undefined, context.subscriptions);
  panel.onDidDispose(() => { panel = undefined; controller?.abort(); }, undefined, context.subscriptions);
}

function update(patch) { if (patch.status) void companion.publish(patch.status); view = { ...view, ...patch }; if (panel) void panel.webview.postMessage(view); }

async function savedKey(endpoint) {
  return await context.secrets.get(api.secretName(endpoint)) || (endpoint.deepseek ? await context.secrets.get(SECRET) : undefined);
}

async function setKey(endpoint = targetEndpoint()) {
  const key = await vscode.window.showInputBox({ title: 'fox · 给AI接口放一把小钥匙 ฅ', prompt: `当前接口：${endpoint.origin}。保存到本机SecretStorage，不发送测试请求。${endpoint.local ? '本机免认证接口可留空。' : '请填写该服务自己的Key，不要求sk前缀。'}`, password: true, ignoreFocusOut: true, validateInput: value => endpoint.local || value.trim().length >= 4 ? null : '请填写该接口的 API Key。' });
  if (key === undefined || (!key.trim() && !endpoint.local)) return false;
  if (key.trim()) await context.secrets.store(api.secretName(endpoint), key.trim());
  else await context.secrets.delete(api.secretName(endpoint));
  vscode.window.showInformationMessage('小钥匙收好啦，喵～配置本身不会发请求，也不会写进项目。');
  return true;
}

async function configureAI() {
  if (running) { vscode.window.showInformationMessage('先等当前讲解结束，或点停止，再换接口哦。'); return; }
  const config = vscode.workspace.getConfiguration('foxMeow');
  const presets=JSON.parse(await fs.readFile(path.join(context.extensionPath,'assets','providers.json'),'utf8'));
  const ordered=['deepseek','custom','local','agnes','openai','anthropic','gemini','qwen','kimi','openrouter-free','groq-free','freellmapi'];
  const provider=await vscode.window.showQuickPick(ordered.map(id=>presets.find(p=>p.id===id)).filter(Boolean).map(p=>({label:p.label,value:p.base||config.get('apiBase','https://api.deepseek.com'),model:p.models?.[0]||'',protocol:p.protocol,description:p.note||p.models?.join(' · ')})),{title:'fox · 选择AI服务商',placeHolder:'支持Agnes、OpenAI、Claude、Gemini及自定义接口；配置不发请求。'});
  if (!provider) return;
  const base = await vscode.window.showInputBox({ title: 'AI 接口地址', prompt: '可填基址、/v1 或完整 /chat/completions。远程需HTTPS。', value: provider.value, ignoreFocusOut: true, validateInput: value => { try { api.resolveEndpoint(value); return null; } catch (e) { return e.message; } } });
  if (!base) return;
  const chosen=await vscode.window.showQuickPick([{label:'Chat Completions',value:'chat'},{label:'Responses API',value:'responses'},{label:'Messages API',value:'messages'}].sort((a,b)=>Number(b.value===provider.protocol)-Number(a.value===provider.protocol)),{title:'选择接入协议',placeHolder:'按服务商文档选择；Agnes支持三种协议。'});
  if(!chosen)return;
  const endpoint = api.resolveEndpoint(base,chosen.value);
  const model = await vscode.window.showInputBox({ title: '模型 ID', prompt: (provider.description||'照服务商给出的模型ID填写；本机模型需先安装。'), value: provider.model, ignoreFocusOut: true, validateInput: value => value.trim() && value.trim().length <= 128 && !/[\r\n]/.test(value) ? null : '请填写有效的模型ID。' });
  if (!model) return;
  await config.update('apiBase', base.trim(), vscode.ConfigurationTarget.Global);
  await config.update('model', model.trim(), vscode.ConfigurationTarget.Global);
  await config.update('protocol',chosen.value,vscode.ConfigurationTarget.Global);
  await setKey(endpoint);
  update({ status: `AI接口已配置为 ${endpoint.origin} / ${model.trim()}，还没有发送代码，喵。` });
}

async function importKnowledge() {
  const files = await vscode.window.showOpenDialog({ title: '导入本地知识库（Markdown / TXT，单篇≤1MB）', canSelectMany: true, filters: { '学习资料': ['md', 'txt'] } });
  if (!files?.length) return;
  if (files.length > 30) throw Error('一次最多导入30篇资料，喵。');
  let count = 0;
  for (const uri of files) {
    const stat = await vscode.workspace.fs.stat(uri);
    if (stat.size > 1024 * 1024) throw Error(`文件过大：${path.basename(uri.fsPath)}。已导入${count}篇。`);
    const text = Buffer.from(await vscode.workspace.fs.readFile(uri)).toString('utf8');
    await knowledge.importDocument(personalKnowledge(), path.basename(uri.fsPath), core.redact(text).text); count++;
  }
  vscode.window.showInformationMessage(`已把${count}篇资料的脱敏副本放进本机知识库，喵～导入不调用AI。启用知识库解析时，匹配片段会附给当前AI接口。`);
}

async function saveKnowledge() {
  const source = await capture('selection');
  const title = await vscode.window.showInputBox({ title: '给这张代码知识小卡片取个名字', value: path.basename(source.filename), validateInput: v => v.trim() && v.length <= 80 ? null : '标题需要1–80个字符。' });
  if (!title) return;
  const text = `# ${title}\n\n来源：${source.filename} 第${source.firstLine}行起\n\n${core.redact(source.text).text}\n`;
  await knowledge.importDocument(personalKnowledge(), title + '.md', text);
  vscode.window.showInformationMessage('小卡片记好啦 ฅ！只存进本机知识库，没有调用AI。');
}

async function searchKnowledge(query) {
  if (typeof query !== 'string') query = await vscode.window.showInputBox({ title: 'fox · 查本地知识库', prompt: '例如：Python函数、async、SQLite、微伴。不调用AI。' });
  if (!query?.trim()) return;
  const hits = await localHits(query);
  const t = openTerminal(); t.start(`ฅ 本地知识库：${query}`);
  if (!hits.length) t.line('这条知识还没找到，喵。可以用「导入」补充Markdown/TXT资料。');
  for (const h of hits) { t.line(`\n【${h.source} · ${h.title}】`); t.line(h.text); }
  t.finish('本次只在本机检索，没有发送AI请求。');
}

async function openKnowledgeFolder() {
  await fs.mkdir(personalKnowledge(), { recursive: true });
  await vscode.commands.executeCommand('revealFileInOS', vscode.Uri.file(personalKnowledge()));
}

function stop() {
  if (controller) { controller.abort(); update({ status: '收到，先停一下喵。已发送的数据无法收回，已处理请求可能仍产生费用。' }); if (terminal?.busy) terminal.line('\n收到停止指令，我先放下小爪子喵。'); }
  else update({ status: '当前没有正在发送的解析请求。' });
}

async function exportNotes() {
  if (!last || !view.notes) { vscode.window.showInformationMessage('还没有可导出的学习笔记，喵。'); return; }
  const uri = await vscode.window.showSaveDialog({ title: '导出中文学习笔记', defaultUri: vscode.Uri.file(path.join(require('node:os').homedir(), `fox-${path.basename(last.filename)}-学习笔记.md`)), filters: { Markdown: ['md'] } });
  if (!uri) return;
  if (last.uri && uri.toString() === last.uri.toString()) { vscode.window.showErrorMessage('导出文件不能覆盖原源码，请选择新的 Markdown 文件。'); return; }
  const text = `# fox 中文代码学习笔记\n\n文件：${last.filename}\n范围：第 ${last.firstLine}–${last.lastLine} 行\n模型：${last.model}\n状态：${view.status}\n\n${view.notes}\n\n---\nAI讲解仅供学习，未经执行验证。Copyright (c) 2026 fox · MIT License\n`;
  await vscode.workspace.fs.writeFile(uri, Buffer.from(text, 'utf8'));
  vscode.window.showInformationMessage('学习笔记已导出。');
}

async function capture(mode) {
  const editor = vscode.window.activeTextEditor || lastEditor;
  if (!editor) throw Error('请先打开一个源码文件，喵。');
  const doc = editor.document;
  lastEditor = editor;
  if (core.isSensitiveFile(doc.fileName)) throw Error('这是密钥或密码配置文件，插件不会发送它。请在源码文件中选择要学习的部分。');
  let range = editor.selection;
  if (mode === 'file') range = new vscode.Range(0, 0, doc.lineCount - 1, doc.lineAt(doc.lineCount - 1).text.length);
  else if (mode === 'function') {
    const symbols = await vscode.commands.executeCommand('vscode.executeDocumentSymbolProvider', doc.uri) || [];
    const possible = [];
    const walk = items => { for (const symbol of items) { const r = symbol.range || symbol.location?.range; if (r?.contains(editor.selection.active) && [vscode.SymbolKind.Function, vscode.SymbolKind.Method, vscode.SymbolKind.Constructor].includes(symbol.kind)) possible.push(r); if (symbol.children) walk(symbol.children); } };
    walk(symbols); possible.sort((a, b) => (a.end.line - a.start.line) - (b.end.line - b.start.line));
    if (!possible.length) throw Error('当前语言服务没有找到光标所在函数。请手动选中代码后解析，喵。');
    range = possible[0];
  } else if (range.isEmpty) throw Error('请先选中你想学习的代码，再点击解析。');
  const text = doc.getText(range);
  if (!text.trim()) throw Error('选区是空白，换一段代码试试喵。');
  return { text, filename: vscode.workspace.asRelativePath(doc.uri, false), language: doc.languageId, firstLine: range.start.line + 1, version: doc.version, document: doc, uri: doc.uri };
}

async function run(mode) {
  if (running) { vscode.window.showInformationMessage('我还在认真读上一段代码喵，先等等或点停止哦～'); return; }
  running = true; controller = new AbortController(); let outputTerminal;
  try {
    if (!vscode.workspace.isTrusted) throw Error('请先确认并信任当前工作区，再发送源码。');
    const source = await capture(mode);
    const config = vscode.workspace.getConfiguration('foxMeow');
    const endpoint = targetEndpoint();
    const max = config.get('maxSourceCharacters', 40000);
    if (source.text.length > max) throw Error(`当前范围共 ${source.text.length} 个字符，超过上限 ${max}。选小一点，我们逐段读懂它喵～`);
    const sanitized = config.get('redactSecrets', true) ? core.redact(source.text) : { text: source.text, count: 0 };
    const chunks = core.chunksOf(sanitized.text, source.firstLine, config.get('linesPerChunk', 80));
    if (chunks.length > config.get('maxRequestsPerAction', 12)) throw Error('这次选区需要太多请求啦，请分成更小的函数或段落学习，避免一次产生过多费用。');
    if (chunks.length > 1) {
      const confirm = await vscode.window.showWarningMessage(`将把 ${source.filename} 的选定范围分为 ${chunks.length} 次AI请求发送到 ${endpoint.origin}，可能产生费用。`, { modal: true }, '开始分段解析');
      if (confirm !== '开始分段解析') return;
    }
    let hits = [];
    if (config.get('useKnowledgeBase', true)) hits = await localHits(source.filename + '\n' + sanitized.text.slice(0, 12000));
    const knowledgeContext = core.redact(knowledge.contextText(hits)).text;
    let key = await savedKey(endpoint);
    if (!key && !endpoint.local) { if (!await setKey(endpoint)) return; key = await savedKey(endpoint); }
    if (!key && !endpoint.local) return;
    if (controller.signal.aborted) return;
    const model = config.get('model', 'deepseek-flash');
    const output = config.get('outputMode', '终端');
    last = { ...source, model, endpoint: endpoint.origin, knowledgeSources: hits.map(h => h.source), lastLine: chunks[chunks.length - 1].lastLine };
    const numbered = sanitized.text.split('\n').map((line, i) => `${source.firstLine + i} | ${line}`).join('\n');
    update({ code: numbered, notes: '', meta: `${source.filename} · 第${source.firstLine}–${last.lastLine}行 · ${endpoint.origin} / ${model} · 本地参考${hits.length}段`, status: `ฅ 认真读代码时间到！共${chunks.length}段${sanitized.count ? `；已隐藏${sanitized.count}处常见敏感值` : ''}。` });
    if (output !== '侧栏') {
      outputTerminal = openTerminal(); outputTerminal.start(`ฅ ${mode === 'suggest' ? '代码建议小课堂' : '代码讲解小课堂'} · ${source.filename} 第${source.firstLine}–${last.lastLine}行`);
      outputTerminal.line(`AI接口：${endpoint.origin} / ${model}`);
      outputTerminal.line(`本地参考：${hits.length ? hits.map(h => h.source + ' / ' + h.title).join('；') : '未匹配相关资料'}`);
      outputTerminal.line('只解释和提出建议，不会执行代码或自动修改文件哦。');
    }
    if (output !== '终端') showPanel();
    let tokenCount = 0;
    for (let i = 0; i < chunks.length; i++) {
      if (controller.signal.aborted) break;
      const c = chunks[i]; const heading = `【第${c.firstLine}–${c.lastLine}行】`;
      update({ status: `喵～正在讲第${i + 1}/${chunks.length}段，慢慢来，我们把它读明白。`, notes: view.notes + `${i ? '\n\n' : ''}${heading}\n` });
      outputTerminal?.line('\n' + heading);
      let lastPaint = 0;
      const result = await api.explain({ key, endpoint: endpoint.url, protocol:endpoint.protocol, auth:config.get('apiAuth','auto'), model, timeoutSeconds: config.get('requestTimeoutSeconds', 120), signal: controller.signal,
        messages: core.makeMessages({ ...source, code: c.text, firstLine: c.firstLine, lastLine: c.lastLine, mode, knowledgeContext, tone: config.get('tone', '元气猫娘'), level: config.get('level', '零基础') }),
        onText: text => { view.notes += text; outputTerminal?.write(text); if (Date.now() - lastPaint > 100) { update({ notes: view.notes }); lastPaint = Date.now(); } }
      });
      update({ notes: view.notes }); tokenCount += result.usage?.total_tokens || 0;
      if (result.finishReason !== 'stop') throw Error(result.finishReason === 'length' ? '这一段输出达到上限啦，已停止后续请求。请缩小选区再解析。' : `本段未正常完成（${result.finishReason}），已停止后续请求。`);
    }
    const status = controller.signal.aborted ? '已停止，保留已有内容；后续段落没有发送。' : `这段代码的小结解开啦，喵～${tokenCount ? ` 本次总用量 ${tokenCount} tokens。` : ''}${source.document.version !== source.version ? '注意：源码已变化，本次笔记对应旧版本。' : ''}`;
    if (!controller.signal.aborted) await context.globalState?.update('companion.lessons', (context.globalState.get('companion.lessons',0)||0)+1);
    update({ status }); outputTerminal?.finish(status);
  } catch (error) {
    const status = controller?.signal.aborted ? '我先停下啦，喵。已有内容保留，没有自动重试。' : (error instanceof Error ? error.message : '解析失败');
    update({ status, notes: view.notes });
    if (outputTerminal) outputTerminal.finish(status);
    else vscode.window.showErrorMessage(status);
  } finally { controller = undefined; running = false; }
}

async function chat(input) {
  if (running) { vscode.window.showInformationMessage('我正在学习代码，先等我一下或点击停止，喵～'); return; }
  const question = typeof input==='string'?input.trim():await vscode.window.showInputBox({title:'和 fox 说说话',prompt:'仅点击确认后发送这段文字到你配置的AI；不会附带编辑器代码。',validateInput:v=>v.trim().length>0&&v.length<=6000?null:'请输入1–6000字。'});
  if (!question) return;
  if(question.length>6000)throw Error('一次最多6000字。');
  if (running) return;
  running=true; controller=new AbortController();
  let t;let answer='';
  try {
    const endpoint=targetEndpoint(); let key=await savedKey(endpoint);
    if (!key&&!endpoint.local) { if (!await setKey(endpoint)) return; key=await savedKey(endpoint); }
    if (controller.signal.aborted) return;
    const config=vscode.workspace.getConfiguration('foxMeow');
    t=openTerminal();t.start('fox 的聊天时间 · '+endpoint.origin);
    t.line('你：'+core.redact(question).text+'\nfox：');
    const result=await api.explain({key,endpoint:endpoint.url,protocol:endpoint.protocol,auth:config.get('apiAuth','auto'),model:config.get('model','deepseek-flash'),signal:controller.signal,timeoutSeconds:config.get('requestTimeoutSeconds',120),messages:[{role:'system',content:'你是fox，温柔可爱的中文猫娘代码学习伙伴。可以说喵但专业准确优先。明确你是软件助手，不声称拥有意识或真实情感。鼓励用户独立学习。只回答用户主动提出的问题。'},{role:'user',content:core.redact(question).text}],onText:text=>{answer+=text;t.write(text);}});
    t.finish(result.finishReason==='stop'?'这次聊天结束啦，喵～':'输出未完整结束，可缩小问题后重试。');
    return {content:answer,complete:result.finishReason==='stop'};
  } catch(e) { if(t)t.finish(e.message||'聊天未完成');else vscode.window.showErrorMessage(e.message);return {error:e.message||'聊天未完成'}; }
  finally {controller=undefined;running=false;}
}

function activate(extensionContext) {
  context = extensionContext;
  const commands = {
    'foxMeow.chat': chat,
    'foxMeow.openHome': () => home.open(vscode, context),
    'foxMeow.openPet': () => companion.launch(context.extensionPath),
    'foxMeow.open': () => openTerminal(),
    'foxMeow.openPanel': () => showPanel(),
    'foxMeow.openTerminal': () => openTerminal(),
    'foxMeow.suggestSelection': () => run('suggest'),
    'foxMeow.configureAI': configureAI,
    'foxMeow.importKnowledge': importKnowledge,
    'foxMeow.saveKnowledge': saveKnowledge,
    'foxMeow.searchKnowledge': () => searchKnowledge(),
    'foxMeow.openKnowledgeFolder': openKnowledgeFolder,
    'foxMeow.explainSelection': () => run('selection'),
    'foxMeow.explainLine': () => run('line'),
    'foxMeow.explainFunction': () => run('function'),
    'foxMeow.explainFile': () => run('file'),
    'foxMeow.setKey': () => setKey(),
    'foxMeow.deleteKey': async () => { const endpoint = targetEndpoint(); await context.secrets.delete(api.secretName(endpoint)); if (endpoint.deepseek) await context.secrets.delete(SECRET); vscode.window.showInformationMessage('当前AI接口的小钥匙已移除。'); },
    'foxMeow.stop': stop,
    'foxMeow.export': exportNotes,
    'foxMeow.settings': () => vscode.commands.executeCommand('workbench.action.openSettings', 'foxMeow')
  };
  for (const [name, callback] of Object.entries(commands)) context.subscriptions.push(vscode.commands.registerCommand(name, async (...args) => { try { return await callback(...args); } catch (e) { vscode.window.showErrorMessage(e.message || '操作未完成'); } }));
  const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 10);
  status.text = '$(heart) fox 陪你学习'; status.command = 'foxMeow.openHome'; status.tooltip = '打开学习面板，不会自动发送代码'; status.show(); context.subscriptions.push(status);
  // Deliberately no editor-selection, document-save, file-watcher, timer or startup network listeners.
}
function deactivate() { controller?.abort(); terminal?.dispose(); }
module.exports = { activate, deactivate };
