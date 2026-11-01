"""Build a signed APK using the installed Android SDK and JDK, no Gradle download."""
from pathlib import Path
import os, subprocess, shutil, json, sqlite3, re, secrets
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parent
SDK=Path(os.environ['LOCALAPPDATA'])/'Android/Sdk'
TOOLS=SDK/'build-tools/36.0.0'
JAR=SDK/'platforms/android-35/android.jar'
JDK=Path(shutil.which('java')).parent
BUILD=ROOT/'build'
ASSETS=BUILD/'assets'
for p in (BUILD,ASSETS,BUILD/'classes',BUILD/'dex'):p.mkdir(parents=True,exist_ok=True)

def run(*args):
    print('Running',Path(str(args[0])).name,flush=True)
    subprocess.run([str(a) for a in args],check=True)

raw=(PROJECT/'answer.js').read_text(encoding='utf-8-sig')
bank=json.loads(re.search(r'const answers\s*=\s*({.*?});',raw,re.S)[1].rstrip().replace(',\n}','\n}'))
rows=[dict(title=q,answer=a,source='页面脚本',kind='选项字母') for q,a in bank.items()]
with sqlite3.connect(PROJECT/'upstream/database.db') as db:
 for ident,answer,title in db.execute('select t.question,t.answer,d.title from tiku t left join tiku_detail d on t.question=d.question'):
  rows.append(dict(title=title or '题目 ID：'+ident,answer=answer,source='GitHub 题库',kind='平台选项 ID'))
(ASSETS/'library.json').write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
shutil.copy(PROJECT/'web/style.css',ASSETS/'style.css')
shutil.copy(PROJECT/'web/adapter.js',ASSETS/'adapter.js')
shutil.copy(PROJECT/'LICENSE',ASSETS/'LICENSE.txt')
shutil.copy(PROJECT/'THIRD_PARTY_NOTICES.md',ASSETS/'THIRD_PARTY_NOTICES.md')
(ASSETS/'index.html').write_text('''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>fox 安全学习</title><link rel="stylesheet" href="/style.css"></head><body><header><div class="brand"><span class="fox">fox</span><span>安全学习<small>内置离线题库</small></span></div><span class="badge">Android 1.1</span></header><main><p class="eyebrow">OFFLINE LIBRARY / 随身检索</p><h1>把安全知识，<br>装进口袋。</h1><p class="muted">题库离线可用。学校平台与实训系统，请点击顶部「连接服务」。</p><form id="searchForm" class="search"><input id="query" aria-label="搜索题目" placeholder="输入题目关键词或 ID"><button>搜索</button></form><div class="filters"><button data-source="all" aria-pressed="true">全部</button><button data-source="页面脚本" aria-pressed="false">页面脚本</button><button data-source="GitHub 题库" aria-pressed="false">GitHub 题库</button></div><p id="summary" class="summary" role="status">正在加载内置题库…</p><div id="results"></div><details class="panel"><summary>使用说明与来源</summary><p>学校平台/实训功能需要 Python 后端运行，手机与电脑同一 Wi-Fi 后输入电脑地址；本 APK 未内置 Python 后端。</p><p>页面脚本：点击顶部「复制脚本」，在支持用户脚本的手机浏览器中导入。修改 @match 为实际答题域名。脚本手动开始，最后手动交卷。</p><p>GitHub 原作者 Scwizard，Apache-2.0。页面题库来自用户提供的 answer.js，保留原作者权利。移动适配与署名 fox。</p><a href="https://github.com/Scwizard/jiangsu-safety-competition/">查看 GitHub 原项目</a></details></main><footer><strong>fox 独家定制</strong> · Copyright © 2026 fox · MIT License</footer><script src="/offline.js"></script></body></html>''',encoding='utf-8')
(ASSETS/'offline.js').write_text('''let rows=[],source='all';const $=id=>document.getElementById(id);function search(){const q=$('query').value.trim().toLowerCase();const matches=rows.filter(r=>(source==='all'||source===r.source)&&r.title.toLowerCase().includes(q));$('summary').textContent='匹配 '+matches.length+' 条 · 内置 '+rows.length+' 条'+(matches.length>100?' · 显示前 100 条':'');$('results').replaceChildren();matches.slice(0,100).forEach(r=>{const a=document.createElement('article');a.className='result';for(const [tag,text,cls]of [['div',r.source+' / '+r.kind,'meta'],['h2',r.title,''],['div','参考答案：'+r.answer,'answer']]){const e=document.createElement(tag);e.textContent=text;e.className=cls;a.append(e)}$('results').append(a)});if(!matches.length)$('results').textContent='没有匹配题目，请尝试更短的关键词。'}$('searchForm').onsubmit=e=>{e.preventDefault();search()};document.querySelectorAll('[data-source]').forEach(b=>b.onclick=()=>{source=b.dataset.source;document.querySelectorAll('[data-source]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));search()});fetch('/library.json').then(r=>r.json()).then(data=>{rows=data;search()}).catch(()=>$('summary').textContent='内置题库加载失败，请重新安装');''',encoding='utf-8')
run(TOOLS/'aapt.exe','package','-f','-M',ROOT/'AndroidManifest.xml','-S',ROOT/'res','-A',ASSETS,'-I',JAR,'-F',BUILD/'resources.apk')
sources=list((ROOT/'src').rglob('*.java'))
run(JDK/'javac.exe','-encoding','UTF-8','-source','8','-target','8','-bootclasspath',str(JAR)+os.pathsep+str(TOOLS/'core-lambda-stubs.jar'),'-d',BUILD/'classes',*sources)
run(TOOLS/'d8.bat','--lib',JAR,'--min-api','26','--output',BUILD/'dex',*list((BUILD/'classes').rglob('*.class')))
shutil.copy(BUILD/'resources.apk',BUILD/'unsigned.apk')
with ZipFile(BUILD/'unsigned.apk','a',ZIP_DEFLATED) as z:
 for p in (BUILD/'dex').glob('*.dex'):z.write(p,p.name)
run(TOOLS/'zipalign.exe','-f','-p','4',BUILD/'unsigned.apk',BUILD/'aligned.apk')
SIGN=Path(os.environ['USERPROFILE'])/'.codex/fox-android-signing'
SIGN.mkdir(parents=True,exist_ok=True)
key=SIGN/'fox-release.jks'
password=SIGN/'password.txt'
if not key.exists():
 password.write_text(secrets.token_urlsafe(32),encoding='utf-8')
 run(JDK/'keytool.exe','-genkeypair','-keystore',key,'-storepass:file',password,'-keypass:file',password,'-alias','fox','-keyalg','RSA','-keysize','3072','-validity','10000','-dname','CN=fox, OU=Mobile, O=fox, C=CN')
run(TOOLS/'apksigner.bat','sign','--ks',key,'--ks-key-alias','fox','--ks-pass','file:'+str(password),'--out',PROJECT/'fox-safety-1.1.0.apk',BUILD/'aligned.apk')
run(TOOLS/'apksigner.bat','verify','--verbose','--print-certs',PROJECT/'fox-safety-1.1.0.apk')
print('APK:',PROJECT/'fox-safety-1.1.0.apk')
