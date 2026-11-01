"""Convertit les cliparts du CD Micro Application « Plus de 50 000 Cliparts Volume 1 » (4366MC) en SVG.
Usage : python3 tools/build_mc.py <dossier Clipart extrait de l'ISO> cliparts/mc"""
import sys,os,glob,json,re,hashlib,unicodedata
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import wmf
src,dst=sys.argv[1],sys.argv[2]
RENAME={'Characters':'Personnages','Christmas':'Noël','Backgrounds':'Arrière-plans','Workout':'Gymnastique','Scenes':'Scènes',
 'Copy of Signes et symboles':'Signes et symboles','Les polices':'Les lettres','Gendermerie marine':'Gendarmerie marine'}
def slug(s):
    s=unicodedata.normalize('NFD',s).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+','-',s).strip('-')
themes={};items=[];seen=set();fails=[];dups=0
for folder in sorted(os.listdir(src),key=lambda s:slug(s)):
    nom=unicodedata.normalize('NFC',folder).replace('’',"'")
    nom=RENAME.get(nom,nom); nom=nom[:1].upper()+nom[1:]
    k=slug(nom)
    for f in sorted(glob.glob(os.path.join(src,folder,'*.WMF'))):
        h=hashlib.md5(open(f,'rb').read()).hexdigest()
        if h in seen: dups+=1; continue
        seen.add(h)
        try: svg=wmf.to_svg(f,True)
        except Exception as e: fails.append((f,repr(e))); continue
        n=os.path.basename(f)[:-4].lower()
        os.makedirs(os.path.join(dst,k),exist_ok=True)
        open(os.path.join(dst,k,n+'.svg'),'w').write(svg)
        themes.setdefault(k,nom); items.append([k,n])
order=sorted(themes,key=lambda k:slug(themes[k]))
idx={k:i for i,k in enumerate(order)}
cat={'source':'Plus de 50 000 Cliparts Volume 1 (Micro Application, réf. 4366MC, 2002), converti depuis WMF',
 'chemin':'cliparts/mc/{dossier}/{n}.svg','themes':[[k,themes[k]] for k in order],
 'items':[[idx[k],n] for k,n in items]}
json.dump(cat,open(os.path.join(dst,'catalog.json'),'w'),ensure_ascii=False,separators=(',',':'))
print('converted',len(items),'themes',len(order),'dups',dups,'fails',len(fails),fails[:5])
