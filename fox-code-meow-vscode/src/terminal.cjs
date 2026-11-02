'use strict';

// User/model text must never be interpreted as terminal control sequences.
function plainTerminal(text) {
  return String(text).replace(/\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\)|.)/g, '')
    .replace(/[\x00-\x08\x0b-\x1f\x7f-\x9f]/g, '').replace(/\r?\n/g, '\r\n');
}

class LearningTerminal {
  constructor(vscode, onCommand, onClose) {
    this.vscode = vscode; this.onCommand = onCommand; this.onClose = onClose;
    this.history = ''; this.input = ''; this.busy = false;
  }
  open() {
    if (this.terminal) { this.terminal.show(true); return; }
    const emitter = new this.vscode.EventEmitter(); this.emitter = emitter;
    const pty = {
      onDidWrite: emitter.event,
      open: () => {
        emitter.fire('\x1b[38;5;216mฅ fox 喵喵代码老师 · 本地知识库学习终端\x1b[0m\r\n');
        emitter.fire('今天也一起把代码读懂吧，喵～\r\n这是学习输出终端，不是 PowerShell，不会执行 shell 命令。\r\n');
        if (this.history) emitter.fire(this.history);
        this.prompt();
      },
      close: () => { this.terminal = undefined; this.promptVisible = false; this.input = ''; emitter.dispose(); if (this.busy) this.onClose(); },
      handleInput: data => this.handleInput(data)
    };
    this.terminal = this.vscode.window.createTerminal({ name: 'fox 喵喵代码老师', pty });
    this.terminal.show(true);
  }
  prompt() { if (this.promptVisible) return; this.input = ''; this.promptVisible = true; if (this.emitter) this.emitter.fire('\r\n\x1b[38;5;182m喵 > \x1b[0m'); }
  write(text) { const value = plainTerminal(text); this.history = (this.history + value).slice(-160000); if (this.terminal && this.emitter) this.emitter.fire(value); }
  line(text = '') { this.write(text + '\n'); }
  start(title) { this.open(); this.promptVisible = false; this.busy = true; this.line('\n────────────────────────────'); this.line(title); }
  finish(status) { this.line('\n' + status); this.busy = false; if (this.terminal) this.prompt(); }
  handleInput(data) {
    if (data === '\x03') { this.input = ''; this.promptVisible = false; this.emitter.fire('^C\r\n'); Promise.resolve(this.onCommand('停止')).finally(() => { if (!this.busy) this.prompt(); }); return; }
    if (data.startsWith('\x1b')) return;
    if (/\bsk-[a-zA-Z0-9_-]{12,}/.test(data)) { this.line('\n密钥请在「配置AI接口」的隐藏输入框填写，不要粘贴到终端哦。'); this.prompt(); return; }
    for (const ch of data.replace(/\r\n/g, '\r')) {
      if (ch === '\r' || ch === '\n') {
        const command = this.input.trim(); this.input = ''; this.promptVisible = false; this.emitter.fire('\r\n');
        if (command) Promise.resolve(this.onCommand(command)).catch(e => this.line(e.message)).finally(() => { if (!this.busy) this.prompt(); });
        else this.prompt();
      } else if (ch === '\x7f' || ch === '\b') {
        if (this.input) { this.input = Array.from(this.input).slice(0, -1).join(''); this.emitter.fire('\b \b'); }
      } else if (ch.charCodeAt(0) >= 32 && this.input.length < 256) { this.input += ch; this.emitter.fire(ch); }
    }
  }
  clear() { this.history = ''; this.promptVisible = false; if (this.emitter) this.emitter.fire('\x1b[2J\x1b[H'); }
  dispose() { this.terminal?.dispose(); this.terminal = undefined; }
}
module.exports = { LearningTerminal, plainTerminal };
