import log,os,sys,re
import threading as th
if not os.path.exists('plugins'):os.mkdir('plugins')
sys.path.append('plugins')
def walktraceback(traceback_object):
    while traceback_object:
        yield re.findall('code .+',str(traceback_object.tb_frame))[0].replace('code ','')[0:-1]
        traceback_object=traceback_object.tb_next
def exout(a, limit=None, file=None):
    print(f'[ThreadException]: {"->".join(walktraceback(a[2]))}:',a[1],mode='ERROR',start='\r')
def print(*args,sep=' ',mode='INFO',end='\n',start=''):
    txt=sep.join(map(str,[*args]))
    sys.stdout.write(txt,mode=mode,end=end,start=start)
_input=input
def input(*args,sep=' ',mode='INPUT',end=''):
    print(*args,sep=sep,mode=mode,end=end)
    return _input()
def loadplugins(*args,run=0):
    if not run:print('Loading plugins...')
    for i in os.listdir('plugins'):
        if i=='__init__.py' or i=='__pycache__':continue
        try:
            tmppl=__import__(f'{i.replace(".py","")}')
            if run:th.Thread(target=tmppl.run,args=(*args,)).start()
            else:
                pl=tmppl.ldp()
                print(f'Loading {pl.get("name",None)} {pl.get("version",None)} Auther:{pl.get("auther",None)}')
                tmppl.init(*args)
        except Exception as err:print(err,mode='ERROR')
th.excepthook=exout
#loadplugins()
#loadplugins(run=1)
