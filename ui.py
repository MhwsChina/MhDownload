import tkinter as tk
import tkinter.ttk as ttk
import os,pystray,sys
import tkinter.messagebox as mess
import threading as th
from PIL import Image
from tkinter import filedialog
from time import sleep
font1,ffg='@Fixedsys','#000000'
ffg1='black'
def getpath(path):
    try:return os.path.join(sys._MEIPASS,path)
    except:return path
def Label(b,font=font1,si=11,**kw):
    return tk.Label(b,**kw,highlightthickness=0,fg=ffg,font=(font,si))
def Listbox(b,font=font1,si=11,**kw):
    return tk.Listbox(b,**kw,highlightthickness=0,fg=ffg,font=(font,si))
def Text(b,font=font1,si=11,**kw):
    return tk.Text(b,**kw,highlightthickness=0,fg=ffg,font=(font,si))
def Button(b,font=font1,si=11,**kw):
    #activebackground='#fba632'
    return tk.Button(b,**kw,highlightthickness=0,activebackground=ffg1,relief='groove',fg=ffg,font=(font,si))
def Entry(b,font=font1,si=11,**kw):
    return tk.Entry(b,**kw,highlightthickness=0,fg=ffg,font=(font,si))
def Combobox(b,font=font1,si=11,**kw):
    return ttk.Combobox(b,**kw,foreground=ffg,background=ffg,font=(font,si))
def Spinbox(b,font=font1,si=11,**kw):
    return ttk.Spinbox(b,**kw,foreground=ffg,font=(font,si))
def Radiobutton(b,font=font1,si=11,**kw):
    return tk.Radiobutton(b,**kw,highlightthickness=0,fg=ffg,font=(font,si),relief='flat')
def Checkbutton(b,font=font1,si=11,**kw):
    return tk.Checkbutton(b,**kw,highlightthickness=0,fg=ffg,font=(font,si),relief='flat')
class _Icon(pystray.Icon):
    def __init__(self,lf,*a,**kw):
        super().__init__(*a,**kw)
        self.lf=lf
    def __call__(self):
        self.lf()
class UI:
    def __init__(self,version,chupdate):
        self.cupd=chupdate
        self.createW(version)
        self.createT(version)
        try:
            if sys.argv[1]=='--hide':self.withdraw()
        except:pass
        self.notify,self.tmpurl=1,tk.StringVar()
    def chupdate(self):
        if not self.cupd():mess.showinfo('MhDown','已是最新版本了!')
    def exit(self):
        t.stop()
        sleep(0.1)
        os._exit(0)
    def askexit(self):
        if mess.askokcancel("MhDown", "退出?"):self.exit()
    def withdraw(self,*a):
        w.state('withdrawn')
        if self.notify:
            t.notify('点击托盘中的下载图标显示窗口','点击托盘中的下载图标显示窗口')
            self.notify=0
    def normal(self,*a):
        w.state('normal')
        w.attributes('-topmost',1)
    def addurl(self):
        if self.url.get():
            dlList.insert('end',self.url.get())
            self.url.set('')
    def delete(self):
        if dlList.curselection():
            dlList.delete(dlList.curselection()[0])
    def log(self,*f):
        self.logt.insert('end',' '.join(map(str,[*f]))+'\n')
        self.logt.see('end')
    def createW(self,version):
        global w,thd,cookie,saveto,prog,state,state1,dlList,timeout,update
        w=tk.Tk()
        w.attributes('-topmost',1)
        w.protocol("WM_DELETE_WINDOW", self.askexit)
        w.bind("<Unmap>", self.withdraw)
        w.resizable(0,0)
        w.title(f'MhDownload{version}')
        fa=tk.Frame(w)###########
        faa=tk.Frame(fa)
        Label(faa,text='网址:    ').pack(side='left')
        self.url=tk.StringVar()
        Entry(faa,width=37,textvariable=self.url).pack(side='left')
        Button(faa,text='添加',command=self.addurl).pack(side='left')
        faa.grid(row=0,column=0,sticky='w')
        fab=tk.Frame(fa)
        Label(fab,text='线程数:  ').pack(side='left')
        thd=tk.IntVar()
        Spinbox(fab,from_=1,to=1024,increment=1,textvariable=thd,width=40).pack(side='left')
        fab.grid(row=1,column=0,sticky='w')
        fac=tk.Frame(fa)
        Label(fac,text='超时时长:').pack(side='left')
        timeout=tk.IntVar()
        Spinbox(fac,from_=1,to=1024,increment=1,textvariable=timeout,width=40).pack(side='left')
        fac.grid(row=2,column=0,sticky='w')
        fad=tk.Frame(fa)
        '''Label(fad,text='Cookie:  ').pack(side='left')
        cookie=Entry(fad,width=42);cookie.pack(side='left')
        fad.grid(row=3,column=0,sticky='w')'''
        fae=tk.Frame(fa)
        Label(fae,text='保存位置:').pack(side='left')
        saveto=tk.StringVar()
        Entry(fae,width=37,textvariable=saveto).pack(side='left')
        Button(fae,text='选择',command=self.setsave).pack(side='left')
        fae.grid(row=3,column=0,sticky='w')
        faf=tk.Frame(fa)
        Label(faf,text='下载进度:').pack(side='left')
        prog=ttk.Progressbar(faf,length=340)
        prog.pack(side='left')
        faf.grid(row=4,column=0,sticky='w')
        fag=tk.Frame(fa)
        state1=tk.StringVar()
        state1.set('正在下载:无')
        Label(fag,textvariable=state1).pack(anchor='w')
        state=tk.StringVar()
        state.set('下载状态:等待中')
        Label(fag,textvariable=state).pack(anchor='w')
        Button(fag,text='取消任务(请用鼠标列表中选择)',command=self.delete).pack(anchor='w')
        self.logt=Text(fag,width=52,height=9)
        self.logt.pack(anchor='w')
        update=tk.IntVar()
        Checkbutton(fag,text='启动时检查更新',variable=update).pack(anchor='w',side='left')
        Button(fag,text='检查更新',command=self.chupdate).pack(anchor='w',side='left')
        Button(fag,text='关于',command=lambda: mess.showinfo('MhDown',f'软件:MhDownload多线程下载器\n作者:_MhwsChina_\n项目:https://github.com/MhwsChina/MhDownload\n开源协议:GPL-3.0\n版本:{version}')).pack(anchor='w')
        fag.grid(row=5,column=0,sticky='w')
        fa.grid(row=0,column=0,padx=10,pady=5,sticky='nw')
        fb=tk.Frame(w)
        Label(fb,text='下载任务列表').pack(anchor='w')
        fba=tk.Frame(fb)
        self.sc1=tk.Scrollbar(fba,orient='vertical')
        self.sc1.pack(side='right',fill='y')
        dlList=Listbox(fba,width=50,height=20,yscrollcommand=self.sc1.set)
        dlList.pack(side='left')
        self.sc1.config(command=dlList.yview)
        fba.pack()
        fb.grid(row=0,column=1,padx=10,pady=5)
    def createT(self,version):
        global t
        menu=pystray.Menu(
            pystray.MenuItem("显示窗口", self.normal),
            pystray.MenuItem("退出", lambda:th.Thread(target=self.exit).start())
        )
        t=_Icon(self.normal,'MhDown',Image.open(getpath('16x16.ico')),f'MhDown {version}',menu)
        self.t_th=th.Thread(target=t.run,daemon=True)
        self.t_th.start()
    def show(self):
        w.mainloop()
    def addurls(self,lll,stp):
        stp.destroy()
        self.normal()
        dlList.insert('end',lll.get())
    def setsave(self):
        p=filedialog.askdirectory()
        if p:saveto.set(p)
    def showaddu(self,url):
        stp=tk.Toplevel(w)
        stp.title('添加下载任务')
        stp.attributes('-topmost',1)
        lll=tk.StringVar();lll.set(url)
        Entry(stp,textvariable=lll,width=52).grid()
        fae=tk.Frame(stp)
        Label(fae,text='保存位置:').pack(side='left')
        Entry(fae,width=37,textvariable=saveto).pack(side='left')
        Button(fae,text='选择',command=self.setsave).pack(side='left')
        fae.grid(sticky='w')
        Button(stp,text='添加下载任务',command=lambda:self.addurls(lll,stp),width=52).grid()
    def addurlw(self,url):
        self.log('接收到下载任务',url)
        th.Thread(target=lambda:self.showaddu(url),name='stp').start()
#ui=UI('beta',lambda:0)
#ui.show()
