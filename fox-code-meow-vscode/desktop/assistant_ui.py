"""Desktop AI UI: all networking follows an explicit Send click."""
import tkinter as tk
from tkinter import filedialog,messagebox,simpledialog
import threading,queue,os
from pathlib import Path
from assistant import Library,save_config,ask

def open_assistant(pet,data):
    if getattr(pet,'assistant_window',None) and pet.assistant_window.winfo_exists():pet.assistant_window.lift();return
    win=tk.Toplevel(pet.root);pet.assistant_window=win;win.title('fox · 文档和聊天');win.geometry('680x620');win.attributes('-topmost',True)
    lib=Library(data/'knowledge-desktop');events=queue.Queue();busy=[False]
    status=tk.StringVar(value='导入和搜索在本机完成；只有点击发送才调用AI。')
    output=tk.Text(win,height=12,wrap='word',font=('Microsoft YaHei',10));output.pack(fill='both',expand=True,padx=12,pady=10)
    def write(text):output.insert('end',str(text)+'\n');output.see('end')
    def task(fn):
        if busy[0]:messagebox.showinfo('fox','等当前操作完成再试哦',parent=win);return
        busy[0]=True;status.set('处理中……')
        def worker():
            try:events.put(('ok',fn()))
            except Exception as e:events.put(('error',str(e)))
        threading.Thread(target=worker,daemon=True).start()
    def poll():
        if not win.winfo_exists():return
        try:
            kind,text=events.get_nowait();busy[0]=False;write(text);status.set('完成啦，喵～' if kind=='ok' else '未完成，可查看上方提示')
        except queue.Empty:pass
        win.after(100,poll)
    def config():
        dialog=tk.Toplevel(win);dialog.title('桌面AI接口');dialog.geometry('520x300');dialog.attributes('-topmost',True)
        values=[]
        for label,default,secret in [('接口URL','https://api.deepseek.com',False),('模型ID','deepseek-chat',False),('API Key','',True)]:
            tk.Label(dialog,text=label).pack(anchor='w',padx=12);entry=tk.Entry(dialog,show='*' if secret else '',width=64);entry.insert(0,default);entry.pack(padx=12,pady=3);values.append(entry)
        def save():
            try:
                if not values[1].get().strip():raise ValueError('请填写模型ID')
                save_config(data,*[e.get() for e in values]);dialog.destroy();write('配置已用Windows用户加密保存，没有发送测试请求。')
            except Exception as e:messagebox.showerror('fox',str(e),parent=dialog)
        tk.Button(dialog,text='加密保存（不发请求）',command=save).pack(pady=12)
    def ingest(folder=False):
        if folder:
            chosen=filedialog.askdirectory(parent=win)
            if not chosen:return
            def paths():
                count=0
                for base,dirs,files in os.walk(chosen,followlinks=False):
                    dirs[:]=[d for d in dirs if d not in ('.git','node_modules','.venv','venv','__pycache__') and not Path(base,d).is_symlink()]
                    for f in files:
                        if count>=1000:return
                        count+=1;yield Path(base,f)
            files=paths()
        else:
            files=filedialog.askopenfilenames(parent=win,title='喂文档（TXT/MD/源码/PDF/DOCX）')
            if not files:return
        task(lambda:'本地导入：成功 %d 篇，跳过 %d 项。原文件保持不变。'%lib.ingest(files))
    def manage():
        dialog=tk.Toplevel(win);dialog.title('知识库副本管理');dialog.geometry('540x370');dialog.attributes('-topmost',True)
        box=tk.Listbox(dialog,selectmode='extended');box.pack(fill='both',expand=True,padx=10,pady=10)
        paths=lib.documents()
        import json
        for p in paths:
            try:box.insert('end',json.loads(p.read_text('utf-8'))['name'])
            except Exception:box.insert('end',p.name)
        def delete(all_items=False):
            selected=paths if all_items else [paths[i] for i in box.curselection()]
            if not selected:return
            if not messagebox.askyesno('永久删除知识库副本',f'永久删除 {len(selected)} 个导入副本？不会删除电脑原文件。',parent=dialog):return
            try:lib.delete(selected);dialog.destroy();write('所选知识库副本已永久清除。')
            except Exception as e:messagebox.showerror('fox',str(e),parent=dialog)
        tk.Button(dialog,text='永久删除选中副本',command=delete).pack(side='left',padx=10,pady=10)
        tk.Button(dialog,text='强制清空全部知识副本',command=lambda:delete(True)).pack(side='left',padx=10)
    def original_menu():
        dialog=tk.Toplevel(win);dialog.title('删除电脑原文件 · 不进回收站');dialog.geometry('540x220');dialog.attributes('-topmost',True)
        tk.Label(dialog,text='此操作永久删除你选中的电脑原文件或文件夹。\n删除后不能从回收站恢复；文件夹中全部内容也会删除。',wraplength=500).pack(padx=12,pady=16)
        force=tk.BooleanVar(value=False)
        tk.Checkbutton(dialog,text='强制模式：清除只读属性后重试（不提权、不结束进程）',variable=force).pack()
        def select(folder=False):
            from file_actions import validate_target,delete_original
            chosen=filedialog.askdirectory(parent=dialog) if folder else filedialog.askopenfilename(parent=dialog)
            if not chosen:return
            try:target=validate_target(chosen)
            except Exception as e:messagebox.showerror('无法删除',str(e),parent=dialog);return
            answer=simpledialog.askstring('永久删除确认',f'目标完整路径：\n{target}\n\n永久删除，不进回收站。确认请输入：DELETE',parent=dialog)
            if answer!='DELETE':return
            mode=force.get()
            task(lambda:'已永久删除原目标：'+delete_original(target,mode))
            dialog.destroy()
        tk.Button(dialog,text='选择原文件并确认删除',command=select).pack(pady=8)
        tk.Button(dialog,text='选择原文件夹并确认删除',command=lambda:select(True)).pack()
    bar=tk.Frame(win);bar.pack(fill='x',padx=12)
    for text,fn in [('配置API',config),('喂文件',lambda:ingest()),('喂文件夹',lambda:ingest(True)),('管理/删除知识库',manage),('删除原文件',original_menu)]:tk.Button(bar,text=text,command=fn).pack(side='left',padx=3)
    question=tk.Text(win,height=4,wrap='word');question.pack(fill='x',padx=12,pady=8)
    use=tk.BooleanVar(value=False);tk.Checkbutton(win,text='附带匹配的本地资料（最多3段，会发送到配置的AI）',variable=use).pack(anchor='w',padx=12)
    def send(local=False):
        q=question.get('1.0','end').strip()
        if not q:return
        if len(q)>6000:messagebox.showinfo('fox','一次最多6000字哦',parent=win);return
        if busy[0]:return
        write('你：'+q)
        # Capture Tk state on UI thread before worker starts.
        include=use.get()
        def work():
            hits=lib.search(q) if include or local else []
            context='\n\n'.join(name+'\n'+text for score,name,text in hits)
            return ('本地参考：\n'+(context or '未找到匹配内容')) if local else 'fox：'+ask(data,q,context)
        task(work)
    buttons=tk.Frame(win);buttons.pack(fill='x',padx=12)
    tk.Button(buttons,text='发送给AI',command=send).pack(side='left');tk.Button(buttons,text='仅本地搜索',command=lambda:send(True)).pack(side='left',padx=8)
    tk.Label(win,textvariable=status,wraplength=640).pack(padx=12,pady=8)
    poll()
