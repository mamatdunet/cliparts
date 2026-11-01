"""Minimal WMF parser/converter for the clipart CDs (Polygon, PolyPolygon, Polyline + pen/brush records)."""
import struct,math
def ellipse_pts(l,t,r,b,a0=0,a1=2*math.pi):
    # polygonal approximation of an ellipse (or of an arc from angle a0 to a1, counter-clockwise on screen)
    cx,cy,rx,ry=(l+r)/2,(t+b)/2,abs(r-l)/2,abs(b-t)/2
    n=max(8,min(72,int((rx+ry)*(a1-a0)/4)))
    return [(round(cx+rx*math.cos(a0+(a1-a0)*i/n)),round(cy-ry*math.sin(a0+(a1-a0)*i/n))) for i in range(n+1)]
def arc_pts(rec,kind):
    ye,xe,ys,xs,b,r,t,l=rec; cx,cy=(l+r)/2,(t+b)/2
    a0=math.atan2(cy-ys,xs-cx); a1=math.atan2(cy-ye,xe-cx)
    if a1<=a0: a1+=2*math.pi
    pts=ellipse_pts(l,t,r,b,a0,a1)
    if kind=='pie': pts=pts+[(round(cx),round(cy))]
    return pts
def round_rect(l,t,r,b,w,h):
    l,r=min(l,r),max(l,r); t,b=min(t,b),max(t,b); rx,ry=min(abs(w)/2,(r-l)/2),min(abs(h)/2,(b-t)/2)
    q=lambda cx,cy,a:ellipse_pts(cx-rx,cy-ry,cx+rx,cy+ry,a,a+math.pi/2)
    return q(r-rx,t+ry,0)+q(l+rx,t+ry,math.pi/2)+q(l+rx,b-ry,math.pi)+q(r-rx,b-ry,3*math.pi/2)
def parse(path,texts=None):
    d=open(path,'rb').read()
    off=0; bbox=None
    if d[:4]==b'\xd7\xcd\xc6\x9a':
        l,t,r,b=struct.unpack_from('<4h',d,6); bbox=(l,t,r,b); off=22
    off+=18
    objs={}; pen=brush=None; org=(0,0); ext=None; shapes=[]; alt=True
    font=None; tcolor=0; talign=0; stack=[]
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
        elif fn==0x2fb:
            h,=struct.unpack_from('<h',d,p); wt,it=struct.unpack_from('<hB',d,p+8)
            face=d[p+18:p+50].split(b'\0')[0].decode('latin-1')
            objs[slot()]=('font',abs(h) or 12,wt,it,face)
        elif fn in (0x0f7,0x142,0x1f9,0x6ff):
            # palettes, pattern brushes, regions: still take an object slot (pattern brushes drawn grey)
            objs[slot()]=('brush',0,0x808080) if fn in (0x142,0x1f9) else ('other',)
        elif fn==0x12d:
            i,=struct.unpack_from('<H',d,p); o=objs.get(i)
            if o and o[0]=='pen':pen=o
            elif o and o[0]=='brush':brush=o
            elif o and o[0]=='font':font=o
        elif fn==0x01e: stack.append((pen,brush,font,tcolor,talign))
        elif fn==0x127:
            n,=struct.unpack_from('<h',d,p)
            for _ in range(-n if n<0 else 1):
                if stack: pen,brush,font,tcolor,talign=stack.pop()
        elif fn==0x209: tcolor=struct.unpack_from('<I',d,p)[0]&0xffffff
        elif fn==0x12e: talign=struct.unpack_from('<H',d,p)[0]
        elif fn in (0x41b,0x418):
            b,r,t,l=struct.unpack_from('<4h',d,p)
            pts=[(l,t),(r,t),(r,b),(l,b)] if fn==0x41b else ellipse_pts(l,t,r,b)
            shapes.append(style(True)+([pts],True,alt))
        elif fn==0x61c:
            h,w,b,r,t,l=struct.unpack_from('<6h',d,p)
            shapes.append(style(True)+([round_rect(l,t,r,b,w,h)],True,alt))
        elif fn in (0x817,0x830,0x81a):
            kind={0x817:'arc',0x830:'chord',0x81a:'pie'}[fn]
            shapes.append(style(kind!='arc')+([arc_pts(struct.unpack_from('<8h',d,p),kind)],kind!='arc',alt))
        elif fn==0x61d:
            h,w,y,x=struct.unpack_from('<4h',d,p+4)
            if brush is not None and brush[1]!=1:
                shapes.append((brush[2],None,0,[[(x,y),(x+w,y),(x+w,y+h),(x,y+h)]],True,alt))
        elif fn in (0x521,0xa32) and texts is not None and font is not None:
            if fn==0x521:
                n,=struct.unpack_from('<h',d,p); txt=d[p+2:p+2+n]; q=p+2+n+(n&1); y,x=struct.unpack_from('<hh',d,q)
            else:
                y,x,n,opt=struct.unpack_from('<hhhH',d,p); q=p+8+(8 if opt&6 else 0); txt=d[q:q+n]
            txt=txt.decode('cp1252',errors='replace').strip('\0')
            if txt.strip(): texts.append((len(shapes),x,y,txt,font,tcolor,talign))
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
def text_geom(t):
    _,x,y,txt,font,color,align=t; h=font[1]
    anchor={6:'middle',2:'end'}.get(align&6,'start')
    base=y if align&24==24 else y-h*0.2 if align&8 else y+h*0.8
    w=h*0.55*len(txt); left=x-w/2 if anchor=='middle' else x-w if anchor=='end' else x
    return h,anchor,base,left,w
def text_box(t):
    h,anchor,base,left,w=text_geom(t)
    return round(left),round(base-h*0.8),round(left+w),round(base+h*0.2)
def text_svg(t,fx,fy):
    _,x,y,txt,font,color,align=t; h,anchor,base,_,_=text_geom(t)
    esc=txt.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    a=['x="%d" y="%d"'%(x*fx,round(base)*fy),'font-size="%d"'%h,'font-family="%s, sans-serif"'%font[4].replace('"','') if font[4] else 'font-family="sans-serif"',
       'fill="%s"'%hexc(color)]
    if fx<0 or fy<0: a.append('transform="scale(%d %d)"'%(fx,fy))
    if anchor!='start': a.append('text-anchor="%s"'%anchor)
    if font[2]>=600: a.append('font-weight="bold"')
    if font[3]: a.append('font-style="italic"')
    return '<text %s>%s</text>'%(' '.join(a),esc)
def to_svg(path,fillrule=False):
    """fillrule=True honours SetPolyFillMode (ALTERNATE → evenodd); False keeps the ClipartsPro output unchanged."""
    texts=[]
    org,ext,bbox,shapes=parse(path,texts)
    # keep the z-order of texts: tag each shape with its index before filtering
    shapes=[s+(i,) for i,s in enumerate(shapes) if (s[0] is not None or s[1] is not None) and any(s[3])]
    # drop leading page rectangles (white page, unfilled coloured frame) so the clipart is transparent;
    # a coloured filled rectangle is a real background and stays
    def is_page(sh,rest):
        if len(sh[3])!=1 or sh[0] not in (None,0xffffff): return False
        pts=set(sh[3][0])
        if len(pts)!=4 or len({x for x,_ in pts})!=2 or len({y for _,y in pts})!=2: return False
        bx0,by0,bx1,by1=bounds([sh]); rx0,ry0,rx1,ry1=bounds(rest)
        return bx0<=rx0+2 and by0<=ry0+2 and bx1>=rx1-2 and by1>=ry1-2
    while len(shapes)>1 and is_page(shapes[0],shapes[1:]): shapes=shapes[1:]
    tboxes=[text_box(t) for t in texts]
    if not shapes and not texts: raise ValueError('empty')
    x0,y0,x1,y1=bounds(shapes+[(None,None,0,[[(a,b),(c,e)]],True,True,0) for a,b,c,e in tboxes])
    m=max(s[2] for s in shapes or [(0,0,0)])//2+2
    x0-=m;y0-=m;x1+=m;y1+=m
    # negative window extents flip the axis (IMSI drawings are stored upside down this way)
    fx=-1 if ext and ext[0]<0 else 1; fy=-1 if ext and ext[1]<0 else 1
    vx=x0 if fx>0 else -x1; vy=y0 if fy>0 else -y1
    root='viewBox="%d %d %d %d" stroke-width="1" stroke-linejoin="round"'%(vx,vy,x1-x0,y1-y0)
    if fillrule: root+=' fill-rule="evenodd"'
    out=['<svg xmlns="http://www.w3.org/2000/svg" %s>'%root]
    if fx<0 or fy<0: out.append('<g transform="scale(%d %d)">'%(fx,fy))
    cur=None; ti=0
    def flush_texts(upto):
        nonlocal cur,ti
        while ti<len(texts) and texts[ti][0]<=upto:
            if cur is not None: out.append('</g>'); cur=None
            out.append(text_svg(texts[ti],fx,fy)); ti+=1
    for fill,stroke,sw,subs,closed,alt,idx in shapes:
        flush_texts(idx)
        key=(fill,stroke,sw,fillrule and not alt)
        if key!=cur:
            if cur is not None: out.append('</g>')
            a=['fill="%s"'%(hexc(fill) if fill is not None else 'none')]
            if stroke is not None: a+=['stroke="%s"'%hexc(stroke)]+(['stroke-width="%d"'%sw] if sw!=1 else [])
            if key[3]: a.append('fill-rule="nonzero"')
            out.append('<g %s>'%' '.join(a)); cur=key
        d=''.join(rel(sub,closed) for sub in subs if sub)
        out.append('<path d="%s"/>'%d)
    flush_texts(1<<30)
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
