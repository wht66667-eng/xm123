"""Warm bubble UI for the local fox assistant. MIT fox."""
import tkinter as tk
from tkinter import filedialog
import threading,queue,os,json
from pathlib import Path
from assistant import Library,save_config,ask

BG='#FFF8EF';CARD='#FFFFFF';INK='#66483B';MUTED='#92766A';PEACH='#FFE1C8';ACCENT='#B95E3B';MINT='#E6F2E8'
def button(parent,text,fn,primary=False):
    b=tk.Button(parent,text=text,command=fn,bg=ACCENT if primary else PEACH,fg='white' if primary else INK,activebackground='#F4C8A7',activeforeground=INK,relief='flat',bd=0,padx=14,pady=8,font=('Microsoft YaHei',10),cursor='hand2',takefocus=True)
    return b

def confirm(parent,title,text,action,typed=False):
    win=tk.Toplevel(parent);win.title(title);win.configure(bg=BG);win.geometry('540x330');win.transient(parent);win.attributes('-topmost',True)
    tk.Label(win,text=title,bg=BG,fg=ACCENT,font=('Microsoft YaHei',15,'bold')).pack(anchor='w',padx=22,pady=(20,10))
    info=tk.Text(win,height=7,wrap='word',bg=CARD,fg=INK,relief='flat',padx=12,pady=10,font=('Microsoft YaHei',10));info.insert('end',text);info.configure(state='disabled');info.pack(fill='both',expand=True,padx=22)
    entry=None
    if typed:
        tk.Label(win,text='确认永久删除，请输入 DELETE',bg=BG,fg=INK).pack(anchor='w',padx=22,pady=(10,0))
        entry=tk.Entry(win,relief='flat',bg=CARD,fg=INK,font=('Microsoft YaHei',11));entry.pack(fill='x',padx=22,pady=5)
    row=tk.Frame(win,bg=BG);row.pack(fill='x',padx=22,pady=16)
    def accept():
        if entry is not None and entry.get()!='DELETE':return
        win.destroy();action()
    button(row,'先不删，留着吧',win.destroy).pack(side='right',padx=5)
    button(row,'确认永久删除',accept,True).pack(side='right')
    win.grab_set()

class Bubbles(tk.Frame):
    def __init__(self,parent):
        super().__init__(parent,bg=BG);self.canvas=tk.Canvas(self,bg=BG,highlightthickness=0);scroll=tk.Scrollbar(self,command=self.canvas.yview);self.canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.canvas.pack(fill='both',expand=True);self.inner=tk.Frame(self.canvas,bg=BG);self.item=self.canvas.create_window(0,0,window=self.inner,anchor='nw');self.inner.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all')));self.canvas.bind('<Configure>',lambda e:self.canvas.itemconfigure(self.item,width=e.width));self.canvas.bind('<MouseWheel>',lambda e:self.canvas.yview_scroll(-int(e.delta/120),'units'))
    def add(self,text,user=False):
        row=tk.Frame(self.inner,bg=BG);row.pack(fill='x',padx=12,pady=8)
        tk.Label(row,text='你' if user else 'fox ฅ',bg=BG,fg=MUTED,font=('Microsoft YaHei',9)).pack(anchor='e' if user else 'w')
        c=tk.Canvas(row,bg=BG,highlightthickness=0,width=470,height=80)
        c.pack(anchor='e' if user else 'w',padx=(32,0) if user else (0,32))
        item=c.create_text(18,14,text=str(text),width=430,anchor='nw',fill=INK,font=('Microsoft YaHei',10));box=c.bbox(item);height=max(54,box[3]+16)
        c.configure(height=height)
        points=[14,0,456,0,470,0,470,14,470,height-14,470,height,456,height,14,height,0,height,0,height-14,0,14,0,0]
        shape=c.create_polygon(points,smooth=True,fill=MINT if user else PEACH,outline='');c.tag_lower(shape)
        menu=tk.Menu(c,tearoff=False);menu.add_command(label='复制这段话',command=lambda:(self.clipboard_clear(),self.clipboard_append(str(text))))
        c.bind('<Button-3>',lambda e:menu.tk_popup(e.x_root,e.y_root));c.bind('<MouseWheel>',lambda e:self.canvas.yview_scroll(-int(e.delta/120),'units'));self.after_idle(lambda:self.canvas.yview_moveto(1))

def open_assistant(pet,data):
    if getattr(pet,'assistant_window',None) and pet.assistant_window.winfo_exists():pet.assistant_window.deiconify();pet.assistant_window.lift();return
    win=tk.Toplevel(pet.root);pet.assistant_window=win;win.title('fox · 陪伴小窝');win.geometry('790x730');win.minsize(740,620);win.configure(bg=BG);win.attributes('-topmost',True)
    lib=Library(data/'knowledge-desktop');events=queue.Queue();busy=[False]
    header=tk.Frame(win,bg=BG);header.pack(fill='x',padx=24,pady=(18,12))
    tk.Label(header,text='fox 的陪伴小窝',font=('Microsoft YaHei',18,'bold'),bg=BG,fg=INK).pack(anchor='w')
    tk.Label(header,text='ฅ 资料慢慢读，问题一点点解开。',font=('Microsoft YaHei',10),bg=BG,fg=MUTED).pack(anchor='w',pady=3)
    body=tk.Frame(win,bg=BG);body.pack(fill='both',expand=True,padx=14)
    nav=tk.Frame(body,bg=BG,width=120);nav.pack(side='left',fill='y',padx=(0,12));area=tk.Frame(body,bg=BG);area.pack(side='left',fill='both',expand=True)
    pages={};tabs={}
    status=tk.StringVar(value='本地导入与搜索不联网；想聊天时再点发送。')
    def show(name):
        for key,page in pages.items():page.pack_forget();tabs[key].configure(bg=PEACH if key==name else BG)
        pages[name].pack(fill='both',expand=True)
    for name in ('聊聊天','喂资料','小钥匙','文件管理'):
        pages[name]=tk.Frame(area,bg=BG);tabs[name]=button(nav,name,lambda n=name:show(n));tabs[name].pack(fill='x',pady=5)
    chat=pages['聊聊天'];bubbles=Bubbles(chat);bubbles.pack(fill='both',expand=True);bubbles.add('欢迎回来呀。可以先喂我一些资料，也可以直接问问题，喵～')
    def write(text):bubbles.add(text)
    def task(fn,done=None):
        if busy[0]:status.set('我还在处理上一件事，稍等一下喵。');return
        busy[0]=True;status.set('小爪子忙碌中……')
        def worker():
            try:events.put((True,fn(),done))
            except Exception as e:events.put((False,str(e),None))
        threading.Thread(target=worker,daemon=True).start()
    def poll():
        if not win.winfo_exists():return
        try:
            ok,text,done=events.get_nowait();busy[0]=False;write(text);status.set('完成啦，喵～' if ok else '这次没完成，详情已放进聊天气泡。')
            if done:done()
        except queue.Empty:pass
        win.after(100,poll)
    use=tk.BooleanVar(value=False)
    tk.Checkbutton(chat,text='附带匹配的资料给AI（最多3段）',variable=use,bg=BG,fg=MUTED,activebackground=BG,selectcolor=CARD).pack(anchor='w',pady=(8,0))
    question=tk.Text(chat,height=3,wrap='word',bg=CARD,fg=INK,relief='flat',padx=12,pady=10,font=('Microsoft YaHei',10));question.pack(fill='x',pady=8)
    def send(local=False):
        q=question.get('1.0','end').strip()
        if not q or busy[0]:return
        if len(q)>6000:status.set('问题稍微短一点哦，一次最多6000字。');return
        include=use.get();bubbles.add(q,True);question.delete('1.0','end')
        def work():
            hits=lib.search(q) if include or local else [];context='\n\n'.join(name+'\n'+text for score,name,text in hits)
            return ('本地参考：\n'+(context or '还没有找到匹配资料，试着喂我一篇吧。')) if local else ask(data,q,context)
        task(work)
    row=tk.Frame(chat,bg=BG);row.pack(fill='x',pady=(0,8));button(row,'发送给 fox',send,True).pack(side='right');button(row,'只查本地资料',lambda:send(True)).pack(side='right',padx=8)
    docs=pages['喂资料'];tk.Label(docs,text='把资料放进小书包',bg=BG,fg=INK,font=('Microsoft YaHei',14,'bold')).pack(anchor='w',pady=10)
    tk.Label(docs,text='TXT · Markdown · 源码 · PDF · Word\n导入副本保存在本机，原文件保持不变。',justify='left',bg=BG,fg=MUTED).pack(anchor='w',pady=8)
    listing=tk.Listbox(docs,selectmode='extended',bg=CARD,fg=INK,selectbackground=PEACH,selectforeground=INK,relief='flat',highlightthickness=0,font=('Microsoft YaHei',10));listing.pack(fill='both',expand=True,pady=10);paths=[]
    def refresh():
        paths[:]=lib.documents();listing.delete(0,'end')
        for p in paths:
            try:listing.insert('end','  '+json.loads(p.read_text('utf-8'))['name'])
            except Exception:listing.insert('end','  '+p.name)
    def ingest(folder=False):
        if busy[0]:return
        if folder:
            chosen=filedialog.askdirectory(parent=win,title='选一个资料文件夹给 fox')
            if not chosen:return
            def iterator():
                count=0
                for base,dirs,files in os.walk(chosen,followlinks=False):
                    dirs[:]=[d for d in dirs if d not in ('.git','node_modules','.venv','venv','__pycache__') and not Path(base,d).is_symlink()]
                    for f in files:
                        if count>=1000:return
                        count+=1;yield Path(base,f)
            files=iterator()
        else:
            files=filedialog.askopenfilenames(parent=win,title='挑几篇文档喂给 fox')
            if not files:return
        task(lambda:'资料收好啦：成功 %d 篇，跳过 %d 项。'%lib.ingest(files),refresh)
    row=tk.Frame(docs,bg=BG);row.pack(fill='x',pady=8)
    button(row,'喂文档',lambda:ingest()).pack(side='left');button(row,'喂文件夹',lambda:ingest(True)).pack(side='left',padx=8)
    def delete_copies(all_items=False):
        selected=list(paths) if all_items else [paths[i] for i in listing.curselection()]
        if not selected:status.set('先挑选需要清理的资料副本喵。');return
        confirm(win,'清理小书包',f'永久清除 {len(selected)} 篇知识库副本。\n电脑上的原文件不会被删除。',lambda:task(lambda:f'已清除 {lib.delete(selected)} 篇副本。',refresh))
    button(row,'删除选中副本',delete_copies).pack(side='left')
    settings=pages['小钥匙'];tk.Label(settings,text='给 fox 一把 AI 小钥匙',bg=BG,fg=INK,font=('Microsoft YaHei',14,'bold')).pack(anchor='w',pady=12)
    cfg={}
    try:cfg=json.loads((data/'desktop-ai.json').read_text('utf-8'))
    except (OSError,ValueError):pass
    values=[]
    for label,value,secret in [('接口地址',cfg.get('url','https://api.deepseek.com'),False),('模型名称',cfg.get('model','deepseek-chat'),False),('API Key（隐藏输入）','',True)]:
        tk.Label(settings,text=label,bg=BG,fg=MUTED).pack(anchor='w',pady=(16,5));e=tk.Entry(settings,show='*' if secret else '',bg=CARD,fg=INK,relief='flat',font=('Microsoft YaHei',11));e.insert(0,value);e.pack(fill='x',ipady=9);values.append(e)
    def save():
        try:
            url,model,key=[e.get().strip() for e in values]
            if not model:raise ValueError('模型名称还没填哦。')
            if not key and cfg.get('key') and url==cfg.get('url'):
                import win32crypt
                key=win32crypt.CryptUnprotectData(bytes.fromhex(cfg['key']),None,None,None,0)[1].decode()
            save_config(data,url,model,key);cfg.update(json.loads((data/'desktop-ai.json').read_text('utf-8')));values[2].delete(0,'end');status.set('小钥匙加密收好啦，没有发送测试请求。')
        except Exception as e:status.set(str(e))
    button(settings,'加密收好小钥匙',save,True).pack(anchor='w',pady=20)
    tk.Label(settings,text='密钥只保存在本机Windows用户加密存储中。\n同一接口留空保存时沿用旧密钥；换接口请填对应密钥。\n仅在聊天页点发送时联网。',bg=BG,fg=MUTED,justify='left',wraplength=440).pack(anchor='w')
    files=pages['文件管理'];tk.Label(files,text='文件整理小角落',bg=BG,fg=INK,font=('Microsoft YaHei',14,'bold')).pack(anchor='w',pady=12)
    tk.Label(files,text='知识库清理只影响副本。\n下面的原文件删除会直接影响电脑文件，且不进回收站。',bg=BG,fg=MUTED,justify='left',wraplength=440).pack(anchor='w',pady=12)
    button(files,'清空全部知识库副本',lambda:delete_copies(True)).pack(anchor='w',pady=10)
    force=tk.BooleanVar(value=False);tk.Checkbutton(files,text='强制模式：清除只读属性后重试',variable=force,bg=BG,fg=INK,activebackground=BG,selectcolor=CARD).pack(anchor='w',pady=(25,8))
    def original(folder=False):
        if busy[0]:return
        from file_actions import validate_target,delete_original
        chosen=filedialog.askdirectory(parent=win,title='选择要永久删除的原文件夹') if folder else filedialog.askopenfilename(parent=win,title='选择要永久删除的原文件')
        if not chosen:return
        try:target=validate_target(chosen)
        except Exception as e:status.set(str(e));return
        mode=force.get();confirm(win,'核对原文件删除',f'目标完整路径：\n{target}\n\n永久删除，不进回收站。文件夹内的全部内容也会删除。',lambda:task(lambda:'已永久删除：'+delete_original(target,mode)),True)
    button(files,'选择原文件并核对',original).pack(anchor='w',pady=8);button(files,'选择原文件夹并核对',lambda:original(True)).pack(anchor='w',pady=8)
    tk.Label(win,textvariable=status,bg=BG,fg=MUTED,wraplength=730,anchor='w',justify='left').pack(fill='x',padx=24,pady=12)
    refresh();show('聊聊天');poll()
