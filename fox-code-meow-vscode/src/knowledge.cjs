'use strict';
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');

function tokens(value) {
  const s = String(value).normalize('NFKC').toLowerCase();
  const out = new Set(s.match(/[a-z_][a-z_0-9]{1,}/g) || []);
  for (const run of s.match(/[\u4e00-\u9fff]+/g) || []) {
    if (run.length === 1) out.add(run);
    else for (let i = 0; i < run.length - 1; i++) out.add(run.slice(i, i + 2));
  }
  return out;
}

function splitDocument(text, source) {
  const lines = text.replace(/\r\n/g, '\n').split('\n');
  let title = path.basename(source); let buffer = []; const result = [];
  function flush() { const content = buffer.join('\n').trim(); if (content) result.push({ source, title, text: content, tokens: tokens(title + '\n' + content) }); buffer = []; }
  for (const line of lines) {
    if (/^#{1,4}\s/.test(line)) { flush(); title = line.replace(/^#+\s*/, ''); }
    if (buffer.join('\n').length + line.length > 1000) flush();
    // Bound very long lines without reading an entire bank as context.
    if (line.length > 1000) { flush(); for (let i = 0; i < Math.min(line.length, 10000); i += 1000) { buffer = [line.slice(i, i + 1000)]; flush(); } }
    else buffer.push(line);
  }
  flush(); return result;
}

async function loadDocuments(roots) {
  const docs = [];
  for (const { dir, label } of roots) {
    let entries;
    try { entries = await fs.readdir(dir, { withFileTypes: true }); }
    catch (e) { if (e.code === 'ENOENT') continue; throw e; }
    for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
      if (docs.length >= 100) return docs;
      if (!entry.isFile() || !/\.(md|txt)$/i.test(entry.name)) continue;
      const file = path.join(dir, entry.name); const stat = await fs.lstat(file);
      if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 1024 * 1024) continue;
      docs.push({ source: label + '/' + entry.name, text: await fs.readFile(file, 'utf8') });
    }
  }
  return docs;
}

function search(documents, query, limit = 3) {
  const q = tokens(query); if (!q.size) return [];
  const chunks = documents.flatMap(d => splitDocument(d.text, d.source));
  const ranked = chunks.map(chunk => {
    let hits = 0;
    for (const t of q) if (chunk.tokens.has(t)) hits += /^[a-z_]/.test(t) ? 2 : 1;
    const titleTokens = tokens(chunk.title);
    for (const t of q) if (titleTokens.has(t)) hits += 1.5;
    return { source: chunk.source, title: chunk.title, text: chunk.text, score: hits / Math.sqrt(4 + chunk.tokens.size) };
  }).filter(x => x.score > 0).sort((a, b) => b.score - a.score || a.source.localeCompare(b.source));
  return ranked.slice(0, limit);
}

function contextText(hits, maxCharacters = 3600) {
  return hits.map((h, i) => `【本地参考${i + 1}：${h.source} / ${h.title}】\n${h.text}`).join('\n\n').slice(0, maxCharacters);
}

async function importDocument(root, filename, text) {
  if (!/\.(md|txt)$/i.test(filename)) throw Error('知识库仅支持 Markdown 和 TXT 文本。');
  if (Buffer.byteLength(text, 'utf8') > 1024 * 1024) throw Error('单篇知识文档不能超过 1MB。');
  await fs.mkdir(root, { recursive: true });
  const base = path.basename(filename).replace(/[^a-zA-Z0-9\u4e00-\u9fff._-]/g, '_');
  const name = `${Date.now()}-${crypto.randomBytes(3).toString('hex')}-${base}`;
  const target = path.join(root, name);
  await fs.writeFile(target, text, { encoding: 'utf8', flag: 'wx' });
  return target;
}

module.exports = { tokens, splitDocument, loadDocuments, search, contextText, importDocument };
