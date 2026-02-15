import requests as req#下载
import threading as th#多线程
import os,shutil,plugin,sys,urllib.parse#文件、插件、日志、url解码
from log import getjs,setjs,updatejs#保存配置，如线程数、超时时长等
from time import sleep,time#停顿
from json import dumps#json转string
from re import findall#正规表达式findall方法,计算文件名
from urllib3 import disable_warnings#取消requests的ssl证书警告
#自定义print和input,不然输出很奇怪
def print(*args,sep=' ',mode='INFO',end='\n',start=''):
    txt=sep.join(map(str,[*args]))
    sys.stdout.write(txt,mode=mode,end=end,start=start)
_input=input
def input(*args,sep=' ',mode='请输入',end=''):
    print(*args,sep=sep,mode=mode,end=end)
    return _input()
disable_warnings()#取消requests的ssl证书警告
jd,lk,ver={},th.Lock(),'b0.001'
hd={
    'User-Agent': f'Mhdl/{ver.replace("b","").replace("v","")}',
    'Accept-Encoding': 'br'
    }#自定义请求头
def fmbt(num):
    if num<=0:return '0字节'
    for a,b in [(1099511627776,'TB'),(1073741824,'GB'),(1048576,'MB'),(1024,'KB'),(1,'字节')]:
        if num>=a:c,d=('%.2f'%(num/a)),b;break
    while c[-1]=='0':c=c[0:-1]
    if c[-1]=='.':c=c[0:-1]
    return c+d
def sum1(ls,ia=lambda a:a):#列表求和，用于计算进度
    t=0
    for i in ls:t+=ia(i)
    return t
#分片计算，如把1024字节的文件分成8份下载就是qp(1024,8)
def qp(a,b):
    l=[[int(a*i/b)+1,int(a*(i+1)/b)] for i in range(b)]
    l[0][0]=0
    return l
def prog(cd=40,n='#',n1='.'):#显示进度
    global jd,ab
    savtmp,oldt,oldtm=os.path.join(saveto,'mhdltmp'),0,time()
    sttm=oldtm
    while ab:
        sleep(0.2)#停顿一下不然一直计算进度占用cpu很大
        if ab==2:ab=0
        if fs and jd:#检测文件总大小是否大于0才输出进度
            t,tm=sum1(list(jd.values()),lambda a:a[1]),time()
            jd1,sp,sp1=t/fs,fmbt((t-oldt)/(tm-oldtm)),fmbt(t/(tm-sttm))
            t1,oldt,oldtm=int(jd1*cd),t,tm
            print(f'[{t1*n}{(cd-t1)*n1}]%.2f%% {sp}/s 平均{sp1}/s     '%(jd1*100),end='',start='\r',mode='PROGRESS')
    print('_',start='\n',end='')
    f_a=open(os.path.join(saveto,save).replace('\\','/'),'wb')#保存
    for f,v in sorted(list(jd.items()),key=lambda i:i[1][2]):
        with open(f,'rb') as f_b:
            print(f'合并{f.replace(savtmp,"")}',start='\r',end='');shutil.copyfileobj(f_b,f_a,16777216)#合并分片文件
        os.remove(f)#移除分片文件
    fs1=f_a.tell()
    f_a.close()
    print('预期大小:',fmbt(fs),f'({fs}字节)','实际大小:',fmbt(fs1),f'({fs1}字节)','文件完整性:',fs==fs1,start='\n');input('下载完毕!\n按Enter退出程序...')
def dl(fn,s,e):
    global jd
    p=os.path.join(saveto,"mhdltmp",f'{s}{e}{fn}')#分片下载临时文件
    jd[p]=[0,0,s,e,0,[]]#进度，格式为[分片的大小,已下载大小,下载起点,下载终点,帮助大小,帮助过自己的线程]
    '''如果某线程下载完了，会帮助其他线程下载。
    计算方法是：把其他没下载完的某一线程的剩余部分取一半来给自己下载
    帮助大小即是若有其他线程帮助后需下载的大小，下载总量达到该值便停止下载'''
    while 1:#循环，若下载出错一直重试
        try:
            if os.path.exists(p):#若下载过了但没下完
                f=open(p,'ab')
                s1=f.tell()
                jd[p][1]=s1#计算新的下载起点
            else:s1,f=0,open(p,'wb')#没下载过
            z1=e-s+1
            if e-s-s1<=0:f.truncate(z1);f.close();break#若下载过了，下完了，结束下载
            jd[p][0]=z1;rs1=req.get(url,headers={**hd, 'Range': f'bytes={s+s1}-{e}'},verify=False,stream=True,timeout=timeout)
            for c in rs1.iter_content(chunk_size=chunks):
                if c:f.write(c);jd[p][1]=f.tell()
                lk.acquire();lk.release()#等待帮助线程开始
                if jd[p][4] and jd[p][1]>=jd[p][4]:#达到帮助大小结束下载
                    f.truncate(jd[p][4]+1);jd[p][1]=f.tell();f.close();break
            if jd[p][1]>z1:f.truncate(z1);f.close()#达到该线程需要下载的总量，即(下载终点-下载起点+1)，结束下载
            break
        except Exception as ex:f.close();print(ex,start='\r',mode='ERROR')#输出下载错误内容
    #帮助其他线程下载
    for f,v in list(jd.items()):
        lk.acquire()
        if v[4] or v[0]<=0 or v[1]>v[0] or v[1]/v[0]>=0.94 or f in jd[p][5]:lk.release();continue
        z,n,sb,eb=v[0:4];bc=(z-n)//2
        if bc<=chunks*2:lk.release();continue
        jd[f][4],ns=n+bc,sb+n+bc+1;jd[f][5].append(p)
        jd[f][0]=jd[f][4]-jd[f][2]
        lk.release()
        print(f'{sb} {eb}/{sb} {sb+n+bc} {sb+n+bc+1} {eb}     ',start='\r')#输出帮助信息
        dl(fn,ns,eb);return
def dl_normal(fn):#不支持断点续传时调用该函数
    global ab,jd
    p=os.path.join(saveto,fn)
    jd[p]=[fs,0,0]
    while 1:
        try:
            rs1=req.get(url,headers=hd,verify=False,stream=True,timeout=timeout)
            with open(p,'wb') as f:
                for c in rs1.iter_content(chunk_size=chunks):
                    f.write(c);jd[p][1]=f.tell()-1
            break
        except req.exceptions.StreamConsumedError:
            rs1=req.get(url,headers=hd,verify=False,timeout=timeout)
        except Exception as ex:print(ex,start='\r',mode='ERROR')
    input('\n下载完毕!')
    os._exit(0)
def inputf(txt,typ=str,ls=[],ifn=None,err='输入错误'):
    while 1:
        tmpa=input(txt)
        if tmpa.replace(' ','')=='':
            if ifn!=None:return ifn
            else:print(err);continue
        try:
            tmpa=typ(tmpa)
            if ls and not tmpa in ls:raise RuntimeError
            return tmpa
        except:print(err)
print('MhDownload(MhD) 多线程下载器')
print(ver,'by _MhwsChina_')
print('上次下载的网址:',getjs(('bf','无')))
print('#########注意###########')
print('#本程序没有UI界面,还在开发中,所以需要用键盘在本窗口输入内容(支持复制粘贴,右键该窗口可粘贴复制的内容)')
print('#若有默认值,留空并回车程序会自动选择默认值')
try:url=sys.argv[1]
except:url=inputf('URL / 网址 -')
timeout=inputf(f'TIMEOUT /超时时长 (默认为{getjs(("timeout",5))})-',int,ifn=getjs("timeout"))
cookie=inputf('Cookie?(留空为无)',ifn='')
if cookie:hd['Cookie']=cookie
while 1:
    #检测跳转
    try:rs=req.head(url,headers=hd,verify=False,timeout=timeout)
    except Exception as ex:print(ex,mode='ERROR');continue
    lc=rs.headers.get('Location',0)
    if lc:hd['Referer'],url=url,lc;print('检测到跳转',lc)
    else:setjs(('bf',url));break
acc=rs.headers.get('Accept-Ranges') == 'bytes'#是否支持断点续传
fs=int(rs.headers.get('Content-Length',0))#文件总大小,0表示未知
#下列代码计算文件名
save1=rs.headers['Content-Disposition'] if 'Content-Disposition' in rs.headers and 'filename' in rs.headers['Content-Disposition'] else url.split('/')[-1]
if 'Content-Disposition' in rs.headers and 'filename' in rs.headers['Content-Disposition']:
    print(rs.headers['Content-Disposition'])
    save1=findall(r'filename=.+;',rs.headers['Content-Disposition'])
    if not save1:save1=findall(r'filename\*="UTF-8\'\'.+',rs.headers['Content-Disposition'])
    if not save1:save1=findall(r'filename\*=UTF-8\'\'.+',rs.headers['Content-Disposition'])
    if not save1:save1=findall(r'filename=".+"',rs.headers['Content-Disposition'])
    if not save1:save1=findall(r'filename=.+',rs.headers['Content-Disposition'])
    save1=save1[0].replace('filename*=','').replace('UTF-8\'\'','').replace('"','').replace(';','').replace('filename=','')
else:save1=os.path.basename(url.split('/')[-1]).split('?')[0]
save1=urllib.parse.unquote(save1)#解码文件名，比如有些时候文件名为"a%20b.c"，解码为"a b.c"
#到此计算文件名结束
print('自动识别文件名:',save1)
print('自动识别文件大小',fmbt(fs),f'({fs}字节)')
save=inputf(f'FILE /保存文件名 (默认为{save1 if save1 else "无"})-',ifn=(save1 if save1 else None))
try:saveto=sys.argv[3]
except:saveto=getjs(("saveto",""));saveto=inputf(f'FOLDER /保存文件夹 (默认为{saveto if saveto else "程序所在文件夹"})-',ifn='').replace('"','')
thd,chunks,threads,ab=inputf(f'THREAD /线程数 (默认为{getjs(("thread",32))})-',int,ifn=getjs("thread")),getjs(("chks",128))*1024,[],1
lps=__import__('__main__')
plugin.loadplugins(lps)#加载插件
try:os.makedirs(os.path.join(saveto,'mhdltmp'))#创建临时文件夹
except:pass
setjs(('timeout',timeout),('thread',thd),('saveto',saveto))
chunks=int(chunks*1024)
plugin.loadplugins(lps,run=1)#运行插件
th.Thread(target=prog).start()#显示进度
if acc:#若支持断点续传便创建多线程
    for tst,te in qp(fs,thd):
        ta=th.Thread(target=dl,args=(save,tst,te))
        ta.start()
        threads.append(ta)
    for ta in threads:ta.join()
else:#不支持断点续传
    print('不支持断点续传!')
    ta=th.Thread(target=dl_normal,args=(save,))
    ta.start()
    ta.join()
ab=2
