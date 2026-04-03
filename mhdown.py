import requests as req#下载
import threading as th#多线程
import os,urllib,config,ui,shutil,extsrv,plugin
from time import time
from math import ceil
from re import findall
import update as upd
req.urllib3.disable_warnings()
ver='v10'
hd={'User-Agent': 'MhDown/'+".".join(findall(r"\d+",ver)),'Accept-Encoding': 'br'}
class mhdown:
    def __init__(self,printc=print):
        self.pr,self.out,self.lk,self.threads={},printc,th.Lock(),[]
    def qp(self,a,b):
        l=[[int(a*i/b)+1,int(a*(i+1)/b)] for i in range(b)]
        l[0][0],l[-1][-1]=0,a-1
        return l
    def dlpart(self,url,s,e,fn,headers=hd,timeout=5,chunk_size=524288,tmpfd='mhdtmp',bzg=[]):
        p=os.path.join(tmpfd,f'{s}-{e}{fn}')
        self.pr[p]=[0,s,e,0,bzg]#[已下载大小,下载起点,下载终点,帮助大小,帮助过的线程]
        while 1:
            try:
                f=open(p,'ab')
                s1=self.pr[p][0]=f.tell()
                z=e-s+1
                if s1>=z:f.truncate(z);break
                rs=req.get(url,headers={**headers,'Range':f'bytes={s+s1}-{e}'},verify=False,timeout=timeout,stream=True)
                for c in rs.iter_content(chunk_size=chunk_size):
                    if c:f.write(c);self.pr[p][0]=f.tell()
                    if self.pr[p][3] and self.pr[p][0]>=self.pr[p][3]:
                        f.truncate(self.pr[p][3]);break
                break
            except Exception as ex:self.out(ex);f.close()
        f.close()
        for f,v in list(self.pr.items()):
            self.lk.acquire()
            if v[0]>=v[2]-v[1]+1 or v[4] or f in self.pr[p][4] or v[0]/(v[2]-v[1]+1)>=0.95:self.lk.release();continue
            t,sb,eb=v[0:3];bz=(eb-sb+1-t)//2
            if bz<=chunk_size:self.lk.release();return
            self.pr[f][3],ns=t+bz,sb+t+bz;self.pr[p][4].append(f)
            self.lk.release()
            self.out(f'{sb} {t+bz-1} {ns} {eb}')
            self.dlpart(url,ns,eb,fn,headers,timeout,chunk_size,tmpfd,self.pr[p][4]);return
    def dlnormal(self,url,fn,headers=hd,timeout=5,chunk_size=524288,saveto='',size=0):
        p=os.path.join(saveto,fn)
        self.pr[p]=[0,0,size]
        while 1:
            try:
                rs=req.get(url,headers=headers,verify=False,stream=True,timeout=timeout)
                with open(p,'wb') as f:
                    for c in rs.iter_content(chunk_size=chunk_size):
                        if c:f.write(c);self.pr[p][0]=f.tell()
                break
            except req.exceptions.StreamConsumedError:
                try:
                    with open(p,'wb') as f:
                        f.write(req.get(url,headers=headers,verify=False,timeout=timeout).content)
                except Exception as ex:self.out(ex)
            except Exception as ex:self.out(ex)
    def thdl(self,url,fn,size,thread=32,headers=hd,timeout=10,chunk_size=524288,tmpfd='mhdtmp',saveto='',acrange=True):
        try:os.makedirs(tmpfd)
        except:pass
        self.pr={};self.threads.clear()
        if not acrange or thread<=1:
            self.dlnormal(url,fn,headers,timeout,chunk_size,saveto,size)
            return
        for s,e in self.qp(size,thread):
            dlth=th.Thread(target=self.dlpart,args=(url,s,e,fn,headers,timeout,chunk_size,tmpfd),name=f'dlpart[{s}-{e}]')
            dlth.start()
            self.threads.append(dlth)
        for dlth in self.threads:dlth.join()
    def redi(self,url,headers=hd,timeout=10):
        while 1:
            try:rs=req.head(url,headers=headers,verify=False,timeout=timeout)
            except Exception as ex:
                self.out(ex)
                url=self.fenxi(url,ex)
                if not url:raise
                continue
            lc=rs.headers.get('Location',0)
            if lc:headers['Referer'],url=url,lc;self.out(f'检测到跳转:{lc}')
            else:return url,rs.headers
    def fenxi(self,url,ex):
        tmp,exname=ex.args[0],ex.__class__.__name__
        while type(tmp)!=str:
            tmp1=tmp.__class__.__name__
            tmp=tmp.args[0]
        if 'MissingSchema'==exname:
            self.out('错误原因:网址前面漏加了http://或https://,程序将自动补全!')
            url1=findall('meant .+',tmp)[0].replace('meant ','')[0:-1]
            self.out('纠正后网址:',url1);return url1
        if 'getaddrinfo failed' in tmp or 'InvalidSchema'==exname or 'InvalidURL'==exname:
            self.out('错误原因:无法解析网址的服务器地址,网址无效!')
            return False
        if exname=='ConnectTimeout':self.out('错误原因:连接超时!')
        if exname=='ReadTimeout':self.out('错误原因:读取超时!')
        return url      
    def fmfn(self,url,headers):
        save1=headers['Content-Disposition'] if 'Content-Disposition' in headers and 'filename' in headers['Content-Disposition'] else url.split('/')[-1]
        if 'Content-Disposition' in headers and 'filename' in headers['Content-Disposition']:
            self.out(headers['Content-Disposition'])
            save1=findall(r'filename=.+;',headers['Content-Disposition'])
            if not save1:save1=findall(r'filename\*="UTF-8\'\'.+',headers['Content-Disposition'])
            if not save1:save1=findall(r'filename\*=UTF-8\'\'.+',headers['Content-Disposition'])
            if not save1:save1=findall(r'filename=".+"',headers['Content-Disposition'])
            if not save1:save1=findall(r'filename=.+',headers['Content-Disposition'])
            save1=save1[0].replace('filename*=','').replace('UTF-8\'\'','').replace('"','').replace(';','').replace('filename=','')
        else:save1=os.path.basename(url.split('/')[-1]).split('?')[0]
        return urllib.parse.unquote(save1)#解码文件名，比如有些时候文件名为"a%20b.c"，解码为"a b.c"
    def clear(self):
        self.pr={};self.threads.clear()
def updatev(*a):
    global timeout,thread,saveto,update
    try:timeout,thread,saveto,update=ui.timeout.get(),ui.thd.get(),ui.saveto.get(),ui.update.get()
    except:return
    config.setjs(('timeout',timeout),('thread',thread),('saveto',saveto),('update',update))
def sum1(ls,ia=lambda a:a):#列表求和，用于计算进度
    t=0
    for i in ls:t+=ia(i)
    return t
def baoliu(num,t='0.01'):
    try:f,f1=str(num).split('.')
    except:f,f1=str(num),''
    if float(t)<1:fl=len(t.split('.')[1]);ff=f1[0:fl];ff+=(fl-len(ff))*'0';return '.'.join([str(f),ff])
    else:ff=f[0:-(int(t)//10)];ff+=(len(f)-len(ff))*'0';return ff
def fmbt(num):
    if num<=0:return '0字节'
    for a,b in [(1099511627776,'TB'),(1073741824,'GB'),(1048576,'MB'),(1024,'KB'),(1,'字节')]:
        if num>=a:c,d=baoliu(num/a),b;break
    while c[-1]=='0':c=c[0:-1]
    if c[-1]=='.':c=c[0:-1]
    return c+d
def fmtime(sec):
    sec=ceil(sec)
    if sec<=0:return '0秒'
    h,m,s=0,0,0
    while sec:
        if sec>=3600:h+=1;sec-=3600;continue
        if sec>=60:m+=1;sec-=60;continue
        s+=sec;break
    return (str(h)+"小时" if h else "")+(str(m)+"分钟" if m else "")+(str(s)+"秒" if (m or h) and s or (not h and not m) and s else "")
def prog():
    if size:ui.prog['maximum'],ui.prog['mode'],otm,sizen=size,'determinate',time(),fmbt(size)
    else:ui.prog['mode']='indeterminate';ui.prog.start(100);ui.state.set('下载状态:还原中')
    ui.state1.set(f'正在下载:{fn}')
    while prg:
        ui.sleep(0.2)
        if size:
            sm,tm=sum1(list(dl.pr.values()),lambda a:a[0]),(time()-otm)
            speed=sm/tm
            sp=(size-sm)/speed if speed else 0
            ui.prog['value']=sm
            ui.state.set(f'下载状态:剩余{fmtime(sp)} {fmbt(speed)}/s {fmbt(sm)}/{sizen}')
    if not size:ui.prog.stop()
def merge():
    f_a=open(os.path.join(saveto,fn).replace('\\','/'),'wb')#保存
    for f,v in sorted(list(dl.pr.items()),key=lambda i:i[1][1]):
        with open(f,'rb') as f_b:
            ui.prog['value']+=1;shutil.copyfileobj(f_b,f_a,16777216)#合并分片文件
        os.remove(f)#移除分片文件
    fs1=f_a.tell();f_a.close()
    if fs1!=size:ui.t.notify(f'{fs1}/{size}','{fn}\n下载不完整!');ui.mess.showwarning('MhDown','下载的文件不完整!')
    else:ui.t.notify(f'{fs1}/{size}',f'{fn}\n下载完成!')
def worker():
    global size,fn,prg
    while 1:
        ui.sleep(2);ui.prog['mode']='determinate';dl.clear()
        if ui.dlList.curselection():sc=ui.dlList.curselection()[0]
        else:sc=0
        url=ui.dlList.get(sc)
        if not url:continue
        ui.dlList.delete(sc);ui.prog['mode']='indeterminate';ui.prog.start(100)
        ui.state.set('下载状态:获取文件信息')
        try:url,hd=dl.redi(url);ui.prog.stop()
        except:ui.state.set('下载状态:获取文件信息失败');ui.prog.stop();continue
        fn,size,acrange,prg=dl.fmfn(url,hd),int(hd.get('Content-Length',0)),hd.get('Accept-Ranges')=='bytes',1
        if not fn:fn=url.replace('/','')
        th.Thread(target=prog).start()
        dl.thdl(url,fn,size,thread,timeout=timeout,saveto=saveto,acrange=acrange);prg=0;ui.sleep(0.2)
        if acrange and thread>1:
            ui.prog['maximum'],ui.prog['mode']=len(dl.pr),'determinate'
            ui.state.set('下载状态:合并文件');merge()
        else:
            if size:
                fs1=list(dl.pr.values())[0][0]
                if fs1!=size:ui.t.notify(f'{fs1}/{size}','{fn}\n下载不完整!');ui.mess.showwarning('MhDown','下载的文件不完整!')
                else:ui.t.notify(f'{fs1}/{size}',f'{fn}\n下载完成!')
            else:ui.t.notify(f'OK',f'{fn}\n下载完成!')
        ui.state.set('下载状态:等待中');ui.state1.set('正在下载:无')
        if isup:ui.mess.showinfo('MhDown','更新完成,请重启程序!');os._exit(0)
def cupd():
    global isup,saveto
    if dl.threads:ui.mess.showinfo('MhDown','还有下载任务未完毕!无法更新!')
    url,size,fn=upd.getupdate(ver,_zip='.py' in ui.sys.argv[0])
    if not url:mainui.log('已是最新版本了!');return False
    if not '.py' in ui.sys.argv[0]:shutil.move(ui.sys.argv[0],'RemoveMe');isup,saveto=1,'';ui.t.notify('将自动下载','发现可用更新');ui.dlList.insert(0,url)
    else:ui.mess.showinfo('MhDown','检测到以源码形式运行,将为你下载最新版本的压缩包!');mainui.addurlw(url)
    return 1
try:os.remove('RemoveMe')
except:pass
timeout,thread,saveto,update=config.getjs(('timeout',5),('thread',32),('saveto',''),('update',1))
mainui,isup=ui.UI(ver,cupd),0
dl=mhdown(mainui.log)
ui.timeout.set(timeout);ui.thd.set(thread);ui.saveto.set(saveto);ui.update.set(update)
ui.timeout.trace_add('write',updatev)
ui.thd.trace_add('write',updatev)
ui.saveto.trace_add('write',updatev)
ui.update.trace_add('write',updatev)
th.Thread(target=worker,daemon=True,name='worker').start()
exts=extsrv.WebSocketServer(send=mainui.addurlw)
extsrv.out=mainui.log
th.Thread(target=exts.start).start()
if update==1:th.Thread(target=cupd,name='checkupdate').start()
plugin.out=mainui.log
sf=__import__('__main__');plugin.loadplugins(sf);plugin.loadplugins(sf,run=1)
mainui.show()
