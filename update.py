import requests as req
from re import findall
from os.path import split
import sys
auther='MhwsChina'
project='MhDownload'
url=f'https://api.github.com/repos/{auther}/{project}/releases'
def getupdate(nowver,find='mhd.exe',_zip=0):
    json=req.get(url,timeout=10,verify=False).json()
    newver=None
    for i in json:
        if 'v' in i['name']:
            newver,dic=float('.'.join(findall(r"\d+",i['name']))),i
            break
    if not newver:return 0,0,0
    if float('.'.join(findall(r"\d+",nowver)))<newver:
        if _zip:return dic['zipball_url'],0,i['name']+'.zip'
        for i in dic['assets']:
            if i['name']==find:
                return i['browser_download_url'],i['size'],split(sys.argv[0])[1]
    return 0,0,0
