"""fox 本地桌面陪伴。MIT © fox. 不读取文件内容、不调用网络。"""
import tkinter as tk
from tkinter import simpledialog
import json, os, time, random, socket, sys
from PIL import Image, ImageTk
from pathlib import Path

DATA = Path(os.environ.get('APPDATA', str(Path.home()))) / 'fox-code-meow'
DATA.mkdir(parents=True, exist_ok=True)
STATE = DATA / 'pet.json'

def load():
    try:
        value = json.loads(STATE.read_text('utf-8'))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}

class Pet:
    def __init__(self):
        self.state = load()
        for key in ('pats','focusMinutes'):
            if not isinstance(self.state.get(key,0),int) or self.state.get(key,0)<0: self.state[key]=0
        self.quiet = bool(self.state.get('quiet',False))
        self.reduce_motion = bool(self.state.get('reduceMotion',False))
        self.root = tk.Tk()
        self.root.title('fox · 桌面陪伴')
        self.root.geometry('300x410+100+100')
        self.root.configure(bg='#fff6e8')
        self.root.attributes('-topmost', True)
        self.sleeping = False
        self.action="wave"; self.action_until=time.monotonic()+2.0; self.frame=0
        asset_root=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parents[1]))/"assets"
        self.frames={name:[ImageTk.PhotoImage(Image.open(asset_root/f"{name}-{i}.png")) for i in range(6)] for name in ("idle","wave","happy","pat","sleep","think")}
        self.focus_end = 0
        self.last_learning = 0
        self.next_sync = 0
        self.sprite_item = None
        self.message = tk.StringVar(value='你好呀！我是 fox，陪你慢慢读懂代码，喵～')
        self.canvas = tk.Canvas(self.root, width=280, height=245, bg='#fff6e8', highlightthickness=0)
        self.canvas.pack(padx=10)
        self.canvas.bind('<ButtonPress-1>', self.press)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.canvas.bind('<ButtonRelease-1>', self.release)
        tk.Label(self.root, textvariable=self.message, bg='#fff6e8', fg='#623c2e', wraplength=265, font=('Microsoft YaHei', 11)).pack(padx=12, pady=5)
        bar = tk.Frame(self.root, bg='#fff6e8'); bar.pack(pady=8)
        for title, callback in [('摸摸', self.pat), ('小鱼干', self.feed), ('休息', self.sleep), ('专注', self.focus)]:
            tk.Button(bar, text=title, command=callback, relief='flat', bg='#ffe0b5', padx=8).pack(side='left', padx=3)
        menu = tk.Menu(self.root, tearoff=False)
        menu.add_command(label='设置我的称呼', command=self.rename)
        menu.add_command(label='置顶 / 取消置顶', command=self.topmost)
        menu.add_command(label='停止专注计时', command=self.stop_focus)
        menu.add_command(label='安静模式 / 恢复联动', command=self.toggle_quiet)
        menu.add_command(label='减少动画 / 恢复动画', command=self.toggle_motion)
        menu.add_command(label='查看陪伴记录', command=self.records)
        menu.add_command(label='最小化（任务栏恢复）', command=self.root.iconify)
        menu.add_command(label='退出 fox', command=self.close)
        self.root.bind('<Button-3>', lambda e: menu.tk_popup(e.x_root,e.y_root))
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.tick()
    def toggle_quiet(self):
        self.quiet=not self.quiet; self.state['quiet']=self.quiet; self.save(); self.message.set('安静模式开启，代码状态不再打扰你。' if self.quiet else '小耳朵上线，恢复代码学习联动！')
    def toggle_motion(self):
        self.reduce_motion=not self.reduce_motion; self.state['reduceMotion']=self.reduce_motion; self.save()
    def records(self):
        self.message.set(f"摸摸 {self.state.get('pats',0)} 次 · 完成专注 {self.state.get('focusMinutes',0)} 分钟。每一点努力都算数，喵～")
    def save(self):
        tmp = STATE.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.state, ensure_ascii=False), 'utf-8'); tmp.replace(STATE)
    def press(self,e): self.anchor=(e.x_root,e.y_root,self.root.winfo_x(),self.root.winfo_y()); self.moved=False
    def drag(self,e):
        x,y,wx,wy=self.anchor; self.moved=True
        self.root.geometry(f'+{max(0,wx+e.x_root-x)}+{max(0,wy+e.y_root-y)}')
    def release(self,e):
        if not self.moved: self.pat()
    def animate(self,name,seconds=2):
        self.action=name; self.action_until=time.monotonic()+seconds; self.frame=0
    def pat(self):
        self.animate("pat")
        self.sleeping=False; self.state['pats']=self.state.get('pats',0)+1; self.save()
        self.message.set(random.choice(['耳朵痒痒的，喵～谢谢你的摸摸！','小爪子准备好了，我们一起进步吧！','遇到难题就拆成小块，我陪着你呀。']))
    def feed(self): self.animate('happy'); self.message.set('小鱼干收好啦！也记得给自己喝一口水，喵～')
    def sleep(self): self.sleeping=not self.sleeping; self.animate('sleep' if self.sleeping else 'wave'); self.message.set('呼噜呼噜……休息也是学习的一部分。' if self.sleeping else '睡醒啦，小耳朵上线！')
    def rename(self):
        name=simpledialog.askstring('fox · 称呼','我该怎么称呼你？',parent=self.root,initialvalue=self.state.get('name',''))
        if name and name.strip(): self.state['name']=name.strip()[:30]; self.save(); self.message.set(f"{self.state['name']}，今天也一起学一点点吧，喵～")
    def topmost(self): self.root.attributes('-topmost',not bool(self.root.attributes('-topmost')))
    def focus(self):
        minutes=simpledialog.askinteger('一起专注','专注几分钟？（1–180）',parent=self.root,minvalue=1,maxvalue=180,initialvalue=25)
        if minutes: self.focus_end=time.monotonic()+minutes*60; self.focus_minutes=minutes; self.message.set('专注开始！我会安静陪着你。再次点击专注可重新计时。')
    def stop_focus(self): self.focus_end=0; self.message.set('计时停止啦，按自己的节奏来。')
    def tick(self):
        try:
            if time.monotonic()<self.next_sync: raise OSError()
            self.next_sync=time.monotonic()+1
            event=json.loads((DATA/'learning.json').read_text('utf-8'))
            if not isinstance(event,dict): event={}
            stamp=event.get('at',0)
            if not self.quiet and isinstance(stamp,(int,float)) and stamp>self.last_learning and time.time()*1000-stamp<120000:
                self.last_learning=stamp
                self.message.set(str(event.get('status',''))[:500])
                self.animate('think' if '正在' in str(event.get('status','')) else 'happy')
        except (OSError,ValueError,TypeError): pass
        c=self.canvas
        action='sleep' if self.sleeping else (self.action if time.monotonic()<self.action_until else 'idle')
        index=0 if self.reduce_motion else (self.frame//2)%6
        if self.sprite_item is None: self.sprite_item=c.create_image(140,122,image=self.frames[action][index])
        else: c.itemconfigure(self.sprite_item,image=self.frames[action][index])
        self.frame+=1
        if self.focus_end and time.monotonic()>=self.focus_end:
            self.focus_end=0; self.state['focusMinutes']=self.state.get('focusMinutes',0)+self.focus_minutes; self.save(); self.message.set('这段专注完成啦！伸个懒腰，看看远处，喵～')
        self.root.after(100,self.tick)
    def close(self): self.save(); self.root.destroy()
    def run(self): self.root.mainloop()

if __name__=='__main__':
    # Windows named mutex: no network listener or extra background service.
    import ctypes
    ctypes.windll.kernel32.CreateMutexW.restype=ctypes.c_void_p
    ctypes.windll.kernel32.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=ctypes.windll.kernel32.CreateMutexW(None,False,'Local\\fox-code-meow-desktop-pet')
    if ctypes.windll.kernel32.GetLastError()!=183:
        try: Pet().run()
        finally:
            if handle: ctypes.windll.kernel32.CloseHandle(handle)

