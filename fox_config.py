"""Copyright (c) 2026 fox. SPDX-License-Identifier: MIT"""
import os
import sys
import json
import getpass
from pathlib import Path

def config_path():
    if getattr(sys,'frozen',False): return Path(sys.executable).parent/'.env'
    own=Path(__file__).resolve().parent/'.env'
    parent=own.parent.parent/'.env'
    return own if own.exists() or not parent.exists() else parent

def load_env():
    path=config_path()
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if not line.strip() or line.lstrip().startswith('#') or '=' not in line: continue
            key,value=line.split('=',1);key=key.strip();value=value.strip()
            if not key.startswith('FOX_'):continue
            if value.startswith('"'):
                try:value=json.loads(value)
                except ValueError:continue
            os.environ.setdefault(key,str(value))

def read_int(name,default,minimum,maximum):
    try:value=int(os.environ.get(name,default))
    except ValueError:raise ValueError(name+' 必须是整数') from None
    if not minimum<=value<=maximum:raise ValueError(name+' 超出允许范围')
    return value

def configure():
    path=config_path();values={}
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if '=' in line and line.startswith('FOX_'):
                k,v=line.split('=',1)
                try:values[k]=str(json.loads(v))
                except ValueError:values[k]=v
    prompts=[('FOX_SCHOOL_KEYWORD','默认学校关键词',''),('FOX_INTERVAL','默认每题间隔（1–120秒）','8'),('FOX_HOST','后端监听地址','127.0.0.1'),('FOX_PORT','后端端口（1–65535）','5080'),('FOX_REQUEST_TIMEOUT','请求超时（5–120秒）','25')]
    for key,label,default in prompts:
        old=values.get(key,default);values[key]=input(f'{label} [{old}]：').strip() or old
    for key,lo,hi in [('FOX_INTERVAL',1,120),('FOX_PORT',1,65535),('FOX_REQUEST_TIMEOUT',5,120)]:
        if not values[key].isdigit() or not lo<=int(values[key])<=hi:raise ValueError(key+' 设置无效，未保存')
    password=getpass.getpass('管理密码（不显示；回车保留现有设置）：')
    if password:
        if len(password)<12:raise ValueError('管理密码至少12位，未保存')
        values['FOX_ADMIN_PASSWORD']=password
    path.write_text('# fox 环境配置 — 不要上传此文件\n'+'\n'.join(k+'='+json.dumps(v,ensure_ascii=False) for k,v in values.items())+'\n',encoding='utf-8')
    print('已保存环境配置：',path,'；请重新启动程序以应用。')

def diagnostics():
    import platform
    import importlib.util
    print('fox 独家定制 | MIT License | Copyright (c) 2026 fox')
    print('系统：',platform.system(),platform.machine(),' | Python：',platform.python_version())
    print('模式：','独立 EXE（无需另装 Python）' if getattr(sys,'frozen',False) else 'Python 源码')
    print('配置文件：',config_path(),' | 已存在：',config_path().exists())
    for module in ['requests','loguru','tqdm']:
        print(module,':', '可用' if importlib.util.find_spec(module) else '未安装，请运行环境配置脚本')
    print('学校关键词：',os.environ.get('FOX_SCHOOL_KEYWORD','未设置'))
    print('后端：',os.environ.get('FOX_HOST','127.0.0.1')+':'+os.environ.get('FOX_PORT','5080'))
    print('管理密码：','已配置' if os.environ.get('FOX_ADMIN_PASSWORD') else '未配置（管理端禁用）')

def startup():
    load_env()
    print('\n'+'='*55+'\nfox 独家定制 · 安全学习控分版\nCopyright (c) 2026 fox · MIT License\n'+'='*55)
    while True:
        action=input('[1] 开始运行  [2] 环境配置  [3] 环境检测  [0] 退出\n请选择 [默认1]：').strip() or '1'
        if action=='1':return
        if action=='0':raise SystemExit()
        if action=='2':
            try:configure()
            except (ValueError,OSError) as exc:print(exc)
        elif action=='3':diagnostics()
        else:print('请输入0至3。')
