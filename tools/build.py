import sys,os,glob,json,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import wmf
src,dst=sys.argv[1],sys.argv[2]
THEMES={'P':('metiers','Métiers & personnages'),'X':('vie','Vie quotidienne'),'M':('maison','Maison & divers'),
 'B':('affaires','Bureau & argent'),'N':('nature','Nature & animaux'),'R':('transports','Transports'),
 'T':('techniques','Techniques & objets'),'S':('sports','Sports & loisirs')}
PERSOS={'F':'','M':'monsieur','W':'madame','Y':'ado','A':'sportif','K':'gamin','D':'dauphin','S':'diablotin',
 'B':'billet','C':'ordinateur','H':'fourmi','G':'serpent','L':'haricot','P':'farfelu'}
ORDER='FMWYAKDSBCHGLP'
def nice(s):
    s=s.strip().replace('’',"'").lower()
    s=re.sub(r'\s+',' ',s)
    return s[:1].upper()+s[1:]
names={}
for line in open(os.path.join(src,'INDEX_3.TXT'),encoding='cp1252'):
    line=line.rstrip('\r\n')
    if len(line)>7: names[line[2:6]]=(line[0],nice(line[7:]))
items=[];fails=[];total=0
for num,(t,nom) in sorted(names.items(),key=lambda kv:kv[1][1]):
    slug=THEMES[t][0]; os.makedirs(os.path.join(dst,slug),exist_ok=True); vs=''
    for v in ORDER:
        f=glob.glob(f'{src}/T*/C*/{t}_{v}_{num}.WMF')
        if not f: continue
        try: svg=wmf.to_svg(f[0])
        except Exception as e: fails.append((f[0],repr(e))); continue
        open(os.path.join(dst,slug,f'{t}_{v}_{num}.svg'.lower()),'w').write(svg); vs+=v; total+=1
    items.append({'n':num,'t':t,'nom':nom,'v':vs})
cat={'source':'Cliparts Pro 12.000 (TLC Domus / Solver S.A., 1996-1998), converti depuis WMF',
 'chemin':'cliparts/{dossier}/{t}_{v}_{n}.svg (en minuscules)',
 'themes':{k:{'dossier':a,'nom':b} for k,(a,b) in THEMES.items()},'persos':PERSOS,'items':items}
json.dump(cat,open(os.path.join(dst,'catalog.json'),'w'),ensure_ascii=False,separators=(',',':'))
print('converted',total,'items',len(items),'fails',fails[:5],len(fails))
