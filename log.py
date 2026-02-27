import sys,time,os
from json import dumps,loads
os.system('')
_write=sys.stdout.write
with open('mhconfig.json','a+') as jfr:
    jfr.seek(0)
    try:js=loads(jfr.read())
    except:js={}
def write(txt,mode=None,b='',end='\n',start=''):
    if txt=='\n':return
    if not txt:return
    m=sys._getframe(1).f_globals['__name__']
    m='' if m=='__main__' else f'[{m}]: '
    t=time.strftime('%H:%M:%S',time.localtime(time.time()))
    if not mode:
        tmp=txt.split('_')[-1]
        if 'pmode' in tmp:
            mode=tmp.replace('pmode','')
            txt=txt.replace('_'+tmp,'')
        else:mode='INFO'
    if not b:
        if mode=='WARN':b='\033[33m'
        if mode=='ERROR' or mode=='ERR':b='\033[31m'
        if mode=='TIPS':b='\033[34m'
        if mode=='SUC' or mode=='SUCCESSFUL':b='\033[32m'
        if mode=='PROG' or mode=='PROGRESS':b='\033[37;42m'
    _write(f'\033[1m{start}{b}[{t} {mode}]: {m}{txt}\033[K\033[0m{end}')
    sys.stdout.flush()
def getjs(*st):
    m,a=sys._getframe(1).f_globals['__name__'],[]
    if not m in js:js[m]={}
    if not [*st]:return js[m]
    for i in [*st]:
        t=i[0] if len(i)==2 else i
        if t in js[m]:a+=[js[m][t]]
        else:
            if len(i)==2:
                js[m][i[0]]=i[1]
                a+=[i[1]]
    if len(a)==1:return a[0]
    return a
def setjs(*st,rt=0):
    a,m=[*st],sys._getframe(1).f_globals['__name__']
    if not a:js[m]={};return
    try:js[m]
    except:js[m]={}
    for i in a:
        try:b,c=i;js[m][b]=c
        except:
            if i in js[m]:del js[m][i]
    with open('mhconfig.json','w') as f:f.write(dumps(js))
    if rt:return js[m]
def updatejs(a):
    js[sys._getframe(1).f_globals['__name__']]=a
    with open('mhconfig.json','w') as f:f.write(dumps(js))
sys.stdout.write=write
