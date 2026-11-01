"""Minimal WMF parser/converter for the clipart CDs (Polygon, PolyPolygon, Polyline + pen/brush records)."""
import struct
def parse(path):
    d=open(path,'rb').read()
    off=0; bbox=None
    if d[:4]==b'\xd7\xcd\xc6\x9a':
        l,t,r,b=struct.unpack_from('<4h',d,6); bbox=(l,t,r,b); off=22
    off+=18
    objs={}; pen=brush=None; org=(0,0); ext=None; shapes=[]; alt=True
    def slot():
        i=0
        while i in objs:i+=1
        return i
    def style(closed):
        fill=None if (not closed or brush is None or brush[1]==1) else brush[2]
        stroke=None if (pen is None or pen[1]==5) else pen[3]
        sw=max(pen[2],1) if stroke is not None else 0
        return fill,stroke,sw
    while off+6<=len(d):
        size,fn=struct.unpack_from('<IH',d,off); p=off+6
        if fn==0 or size<3:break
        if fn==0x2fa:
            st,w,_,c=struct.unpack_from('<HhhI',d,p); objs[slot()]=('pen',st&0xf,w,c&0xffffff)
        elif fn==0x2fc:
            st,c,_=struct.unpack_from('<HIH',d,p); objs[slot()]=('brush',st,c&0xffffff)
        elif fn==0x12d:
            i,=struct.unpack_from('<H',d,p); o=objs.get(i)
            if o and o[0]=='pen':pen=o
            elif o and o[0]=='brush':brush=o
        elif fn==0x1f0:
            i,=struct.unpack_from('<H',d,p); objs.pop(i,None)
        elif fn==0x106: alt=struct.unpack_from('<H',d,p)[0]!=2
        elif fn==0x20b: y,x=struct.unpack_from('<hh',d,p); org=(x,y)
        elif fn==0x20c: h,w=struct.unpack_from('<hh',d,p); ext=(w,h)
        elif fn in (0x324,0x325):
            n,=struct.unpack_from('<h',d,p); pts=struct.unpack_from('<%dh'%(2*n),d,p+2)
            closed=fn==0x324
            shapes.append(style(closed)+([list(zip(pts[::2],pts[1::2]))],closed,alt))
        elif fn==0x538:
            k,=struct.unpack_from('<h',d,p); ns=struct.unpack_from('<%dh'%k,d,p+2); q=p+2+2*k; subs=[]
            for n in ns:
                pts=struct.unpack_from('<%dh'%(2*n),d,q); q+=4*n; subs.append(list(zip(pts[::2],pts[1::2])))
            shapes.append(style(True)+(subs,True,alt))
        off+=size*2
    return org,ext,bbox,shapes
def hexc(c):
    r,g,b=c&255,(c>>8)&255,(c>>16)&255
    s='%02x%02x%02x'%(r,g,b)
    return '#'+(s[0]+s[2]+s[4] if s[0]==s[1] and s[2]==s[3] and s[4]==s[5] else s)
def bounds(shapes):
    xs=[x for s in shapes for sub in s[3] for x,_ in sub]; ys=[y for s in shapes for sub in s[3] for _,y in sub]
    return min(xs),min(ys),max(xs),max(ys)
def rel(pts,closed=True):
    # absolute first point, then relative lineto; drop separators before negatives
    o=['M%d %d'%pts[0]]; px,py=pts[0]; seg=[]
    for x,y in pts[1:]:
        if (x,y)==(px,py): continue
        seg+=[x-px,y-py]; px,py=x,y
    if seg:
        t='l'
        for i,v in enumerate(seg):
            t+=('' if i==0 or v<0 else ' ')+str(v)
        o.append(t)
    return ''.join(o)+('z' if closed else '')
def to_svg(path,fillrule=False):
    """fillrule=True honours SetPolyFillMode (ALTERNATE → evenodd); False keeps the ClipartsPro output unchanged."""
    org,ext,bbox,shapes=parse(path)
    shapes=[s for s in shapes if (s[0] is not None or s[1] is not None) and any(s[3])]
    # drop leading page rectangles (white page, coloured frame) so the clipart is transparent
    def is_page(sh,rest):
        if len(sh[3])!=1: return False
        pts=set(sh[3][0])
        if len(pts)!=4 or len({x for x,_ in pts})!=2 or len({y for _,y in pts})!=2: return False
        bx0,by0,bx1,by1=bounds([sh]); rx0,ry0,rx1,ry1=bounds(rest)
        return bx0<=rx0+2 and by0<=ry0+2 and bx1>=rx1-2 and by1>=ry1-2
    while len(shapes)>1 and is_page(shapes[0],shapes[1:]): shapes=shapes[1:]
    if not shapes: raise ValueError('empty')
    x0,y0,x1,y1=bounds(shapes); m=max(s[2] for s in shapes)//2+2
    x0-=m;y0-=m;x1+=m;y1+=m
    # negative window extents flip the axis (IMSI drawings are stored upside down this way)
    fx=-1 if ext and ext[0]<0 else 1; fy=-1 if ext and ext[1]<0 else 1
    vx=x0 if fx>0 else -x1; vy=y0 if fy>0 else -y1
    root='viewBox="%d %d %d %d" stroke-width="1" stroke-linejoin="round"'%(vx,vy,x1-x0,y1-y0)
    if fillrule: root+=' fill-rule="evenodd"'
    out=['<svg xmlns="http://www.w3.org/2000/svg" %s>'%root]
    if fx<0 or fy<0: out.append('<g transform="scale(%d %d)">'%(fx,fy))
    cur=None
    for fill,stroke,sw,subs,closed,alt in shapes:
        key=(fill,stroke,sw,fillrule and not alt)
        if key!=cur:
            if cur is not None: out.append('</g>')
            a=['fill="%s"'%(hexc(fill) if fill is not None else 'none')]
            if stroke is not None: a+=['stroke="%s"'%hexc(stroke)]+(['stroke-width="%d"'%sw] if sw!=1 else [])
            if key[3]: a.append('fill-rule="nonzero"')
            out.append('<g %s>'%' '.join(a)); cur=key
        d=''.join(rel(sub,closed) for sub in subs if sub)
        out.append('<path d="%s"/>'%d)
    if cur is not None: out.append('</g>')
    if fx<0 or fy<0: out.append('</g>')
    out.append('</svg>')
    return ''.join(out)
def to_png(path,size=160):
    from PIL import Image,ImageDraw
    org,ext,bbox,shapes=parse(path)
    x0,y0,x1,y1=bounds(shapes); s=(size-4)/max(x1-x0,y1-y0,1)
    im=Image.new('RGB',(size,size),'white'); dr=ImageDraw.Draw(im)
    rgb=lambda c:(c&255,(c>>8)&255,(c>>16)&255)
    for fill,stroke,sw,subs,closed,alt in shapes:
        for sub in subs:
            P=[((x-x0)*s+2,(y-y0)*s+2) for x,y in sub]
            if len(P)<2:continue
            if closed: dr.polygon(P,fill=rgb(fill) if fill is not None else None,outline=rgb(stroke) if stroke is not None else None)
            elif stroke is not None: dr.line(P,fill=rgb(stroke))
    return im
