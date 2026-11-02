"""fox 本地桌面陪伴。MIT © fox. 文档导入在本机；AI仅主动发送时调用。"""
import tkinter as tk
from tkinter import simpledialog
import json, os, time, random, socket, sys
from PIL import Image, ImageTk
from pathlib import Path
import assistant_ui, file_actions

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
        self.root.geometry('240x240+300+300')
        self.root.overrideredirect(True)
        self.root.attributes('-transparentcolor','#ff00ff')
        self.pos_x=300;self.pos_y=300;self.roaming=True; self.dragging=False; self.direction=1; self.move_until=0; self.pause_until=time.monotonic()+2; self.bubble_until=0
        self.root.configure(bg='#ff00ff')
        self.root.attributes('-topmost', True)
        self.sleeping = False
        self.action="idle"; self.action_until=0; self.frame=0
        asset_root=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parents[1]))/"assets"
        self.frames={name:[ImageTk.PhotoImage(Image.open(asset_root/f"{name}-{i}.png")) for i in range(6)] for name in ("idle","wave","happy","pat","sleep","think")}
        self.walk_left=[ImageTk.PhotoImage(Image.open(asset_root/f"wave-{i}.png").transpose(Image.Transpose.FLIP_LEFT_RIGHT)) for i in range(6)]
        self.focus_end = 0
        self.last_learning = 0
        self.next_sync = 0
        self.sprite_item = None
        self.message = tk.StringVar(value='你好呀！我是 fox，陪你慢慢读懂代码，喵～')
        self.canvas = tk.Canvas(self.root, width=240, height=240, bg='#ff00ff', highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind('<ButtonPress-1>', self.press)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.canvas.bind('<ButtonRelease-1>', self.release)
        self.bubble=tk.Toplevel(self.root); self.bubble.withdraw(); self.bubble.overrideredirect(True); self.bubble.attributes('-topmost',True)
        tk.Label(self.bubble,textvariable=self.message,bg='#fff6e8',fg='#623c2e',wraplength=230,padx=12,pady=8,font=('Microsoft YaHei',10)).pack()
        self.message.trace_add('write',self.show_bubble)
        menu = tk.Menu(self.root, tearoff=False)
        menu.add_command(label='聊天 / 文档 / API / 删除知识库', command=self.open_assistant)
        menu.add_command(label='摸摸头',command=self.pat)
        menu.add_command(label='投喂小鱼干',command=self.feed)
        menu.add_command(label='休息 / 睡醒',command=self.sleep)
        menu.add_command(label='开始专注',command=self.focus)
        menu.add_command(label='自由走动 / 原地停留',command=self.toggle_roam)
        menu.add_command(label='设置我的称呼', command=self.rename)
        menu.add_command(label='置顶 / 取消置顶', command=self.topmost)
        menu.add_command(label='停止专注计时', command=self.stop_focus)
        menu.add_command(label='安静模式 / 恢复联动', command=self.toggle_quiet)
        menu.add_command(label='减少动画 / 恢复动画', command=self.toggle_motion)
        menu.add_command(label='查看陪伴记录', command=self.records)
        menu.add_command(label='暂时隐藏5秒', command=lambda:(self.root.withdraw(),self.root.after(5000,self.root.deiconify)))
        menu.add_command(label='退出 fox', command=self.close)
        self.root.bind('<Button-3>', lambda e: menu.tk_popup(e.x_root,e.y_root))
        self.root.bind('<Double-Button-1>',lambda e:self.open_assistant())
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.tick()
    def toggle_roam(self):
        self.roaming=not self.roaming
    def show_bubble(self,*args):
        if time.monotonic()>self.bubble_until:return
        if getattr(self,"bubble_callback",None):self.bubble_callback(self.message.get());return
        self.bubble.geometry(f'+{max(0,self.pos_x)}+{max(0,self.pos_y-80)}');self.bubble.deiconify()
        self.root.after(3500,self.bubble.withdraw)
    def open_assistant(self):
        if getattr(self,"assistant_callback",None):self.assistant_callback();return
        from assistant_ui import open_assistant
        open_assistant(self,DATA)
    def toggle_quiet(self):
        self.quiet=not self.quiet; self.state['quiet']=self.quiet; self.save(); self.message.set('安静模式开启，代码状态不再打扰你。' if self.quiet else '小耳朵上线，恢复代码学习联动！')
    def toggle_motion(self):
        self.reduce_motion=not self.reduce_motion; self.state['reduceMotion']=self.reduce_motion; self.save()
    def records(self):
        self.message.set(f"摸摸 {self.state.get('pats',0)} 次 · 完成专注 {self.state.get('focusMinutes',0)} 分钟。每一点努力都算数，喵～")
    def save(self):
        tmp = STATE.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.state, ensure_ascii=False), 'utf-8'); tmp.replace(STATE)
    def press(self,e): self.anchor=(e.x_root,e.y_root,self.root.winfo_x(),self.root.winfo_y()); self.moved=False; self.dragging=True; self.pause_until=time.monotonic()+5
    def drag(self,e):
        x,y,wx,wy=self.anchor; self.moved=True
        self.root.geometry(f'+{max(0,wx+e.x_root-x)}+{max(0,wy+e.y_root-y)}')
    def release(self,e):
        self.dragging=False; self.pause_until=time.monotonic()+5
        if not self.moved: self.pat()
    def animate(self,name,seconds=2):
        self.action=name; self.action_until=time.monotonic()+seconds; self.frame=0; self.bubble_until=time.monotonic()+4; self.pause_until=time.monotonic()+4; self.move_until=0
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
        if minutes: self.bubble_until=time.monotonic()+4; self.focus_end=time.monotonic()+minutes*60; self.focus_minutes=minutes; self.message.set('专注开始！我会安静陪着你。再次点击专注可重新计时。')
    def stop_focus(self): self.focus_end=0; self.message.set('计时停止啦，按自己的节奏来。')
    def tick(self):
        c=self.canvas
        now=time.monotonic();walking=False
        if self.roaming and not self.sleeping and not self.dragging and now>self.pause_until:
            if now>self.move_until:
                self.direction=random.choice([-1,1]);self.move_until=now+random.uniform(2,5);self.pause_until=self.move_until+random.uniform(2,4)
            walking=True
        elif self.roaming and now<self.move_until and not self.dragging and not self.sleeping:walking=True
        if walking:
            x=self.pos_x+self.direction*3;y=self.pos_y;limit=max(0,self.root.winfo_screenwidth()-240)
            if x<0 or x>limit:self.direction*=-1;x=max(0,min(limit,x))
            self.pos_x=x;self.pos_y=max(0,min(self.root.winfo_screenheight()-280,y));self.root.geometry(f'+{self.pos_x}+{self.pos_y}')
        action='sleep' if self.sleeping else (self.action if now<self.action_until else ('wave' if walking else 'idle'))
        index=0 if self.reduce_motion or (action=='idle') else (self.frame//2)%6
        image=self.walk_left[index] if walking and self.direction<0 and action=='wave' else self.frames[action][index]
        if self.sprite_item is None: self.sprite_item=c.create_image(120,120,image=image)
        else: c.itemconfigure(self.sprite_item,image=image)
        self.render_action=action; self.render_index=index
        self.frame+=1
        if self.focus_end and time.monotonic()>=self.focus_end:
            self.focus_end=0; self.state['focusMinutes']=self.state.get('focusMinutes',0)+self.focus_minutes; self.save(); self.message.set('这段专注完成啦！伸个懒腰，看看远处，喵～')
        self.root.after(80,self.tick)
    def close(self): self.save(); self.root.destroy()
    def run(self): self.root.mainloop()

if __name__=='__main__':
    if '--self-test' in sys.argv:
        result_path=Path(sys.argv[sys.argv.index('--self-test')+1])
        try:
            from selftest import run as selftest_run
            selftest_run(result_path)
        except Exception:
            import traceback
            result_path.write_text(json.dumps({'ok':False,'error':traceback.format_exc()}),'utf-8')
            raise
        raise SystemExit(0)
    # Windows named mutex: no network listener or extra background service.
    import ctypes
    ctypes.windll.kernel32.CreateMutexW.restype=ctypes.c_void_p
    ctypes.windll.kernel32.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=ctypes.windll.kernel32.CreateMutexW(None,False,'Local\\fox-code-meow-desktop-pet')
    if ctypes.windll.kernel32.GetLastError()!=183:
        try:
            from qt_pet import run
            run()
        finally:
            if handle: ctypes.windll.kernel32.CloseHandle(handle)

