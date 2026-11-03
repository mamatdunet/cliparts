"""Lit les catalogues .cag de la Clip Gallery d'Office 97 : un fichier composé OLE avec trois flux.
Category : pour chaque catégorie, un numéro (u32), la longueur du nom (u8), le nom, le nombre d'images (u16), BE EE EB BE,
           puis les numéros (u32) des images. Un nom finissant par \\x01\\x01 appartient à l'onglet Pictures, les autres à Clip Art.
Thumb    : la fiche de l'image n est à l'octet n × 400 : 4 octets, puis nom du fichier, chemin et mots-clés, chacun précédé de sa longueur (u8).
Nail     : les vignettes."""
import re, struct

MARQUE = b'\xbe\xee\xeb\xbe'


def flux(chemin):
    """{nom : contenu} des flux d'un fichier composé OLE."""
    b = open(chemin, 'rb').read()
    ss, ms = 1 << struct.unpack('<H', b[30:32])[0], 1 << struct.unpack('<H', b[32:34])[0]
    nfat, dirs, _, seuil, mfat, _, dif, _ = struct.unpack('<8I', b[44:76])
    sect = lambda i: b[(i + 1) * ss:(i + 2) * ss]
    tete = list(struct.unpack('<109I', b[76:512]))
    while dif < 0xfffffffe:
        x = struct.unpack(f'<{ss // 4}I', sect(dif)); tete += x[:-1]; dif = x[-1]
    fat = []
    for i in tete[:nfat]:
        fat += struct.unpack(f'<{ss // 4}I', sect(i))
    def chaine(s):
        o = bytearray()
        while s < 0xfffffffe:
            o += sect(s); s = fat[s]
        return bytes(o)
    rep = chaine(dirs)
    entrees = []
    for i in range(0, len(rep), 128):
        e = rep[i:i + 128]; l = struct.unpack('<H', e[64:66])[0]
        if l:
            entrees.append((e[:l - 2].decode('utf-16le'), e[66], struct.unpack('<I', e[116:120])[0], struct.unpack('<I', e[120:124])[0]))
    mini = chaine(next(e for e in entrees if e[1] == 5)[2])
    m = chaine(mfat) if mfat < 0xfffffffe else b''
    mf = struct.unpack(f'<{len(m) // 4}I', m)
    def petite(s, n):
        o = bytearray()
        while s < 0xfffffffe:
            o += mini[s * ms:(s + 1) * ms]; s = mf[s]
        return bytes(o[:n])
    return {nom: chaine(d)[:t] if t >= seuil else petite(d, t) for nom, ty, d, t in entrees if ty == 2}


def lire(chemin):
    """(catégories {nom : [numéros]}, fiches {numéro : (fichier, mots-clés)}) de l'onglet Clip Art."""
    f = flux(chemin)
    c, t = f['Category'], f['Thumb']
    tetes = []
    for m in re.finditer(re.escape(MARQUE), c):
        i = m.start()
        for L in range(1, 40):
            j = i - 3 - L
            if j >= 4 and c[j] == L and all(32 <= x < 127 or x < 4 for x in c[j + 1:j + 1 + L]) and 1000 <= struct.unpack('<I', c[j - 4:j])[0] < 1200:
                tetes.append((j - 4, i + 4, c[j + 1:j + 1 + L].decode('latin1'))); break
    cats = {}
    for k, (a, b, nom) in enumerate(tetes):
        e = tetes[k + 1][0] if k + 1 < len(tetes) else len(c)
        cats[nom] = struct.unpack(f'<{(e - b) // 4}I', c[b:b + (e - b) // 4 * 4])
    fiches = {}
    for i in cats.get('(All Categories)', ()):
        o = i * 400 + 4
        L = t[o]; nom = t[o + 1:o + 1 + L].decode('latin1'); o += 1 + L
        o += 1 + t[o]
        fiches[i] = (nom, t[o + 1:o + 1 + t[o]].decode('latin1').strip())
    return {n: [i for i in v if i in fiches] for n, v in cats.items() if n != '(All Categories)' and not n.endswith('\x01\x01')}, fiches
