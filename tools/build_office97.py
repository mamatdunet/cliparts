"""Importe les cliparts de Microsoft Office 97 (« Microsoft Clipart Extra », archive.org/details/mso97clipart).
Usage : python3 tools/build_office97.py <SVG-LibreOffice extrait du zip> <Clipart extrait de Clipart.zip>

Le zip contient les WMF du CD convertis en SVG avec LibreOffice Draw 6.4 par dbohdan : on retire ce que l'export ajoute
(masques de page, puces, identifiants, données d'Inkscape). Les fichiers n'ont qu'un nom court (reindr1, trkeyfun…) qui
sert de nom au dessin et choisit la rubrique : voir SUJETS, un dessin va dans cliparts/office97/<rubrique>/<nom>.svg.
Les 4 dossiers du CD (Office, Popular, Powerpnt, Scrbeans) deviennent des mots-clés, avec ceux de la Clip Gallery (Clipart.zip, .cag)."""
import sys, os, re, json, shutil, hashlib
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_openclipart import nettoyer, FR, NOMS, SLUGS
import cag
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1]
dst = os.path.join(root, 'cliparts/office97')
SVG = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG)
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
DOSSIERS = {'Office': 'bureautique', 'Popular': 'populaires', 'Powerpnt': 'powerpoint', 'Scrbeans': 'screen beans personnages'}

PAYS = ('usflag uscalif thailnd flgpirat gldngate north africa albania andorra argentin argntin armenia astrlia austr ausschil azerbaij azrbaij belarus belgium blgfranc bosnia brazil brunei bulgari camerica canada china cis croatia '
        'cuba cyprus czech denmark denmk egypt england eurasia europe eurunion estonia finland france georgia germany greece hongkon hungary iceland india ireland israel italy japan kazakhs '
        'kyrgyzs latvia liechten liechts lithuan lithuani luxemb macedn macedon malta mexico midleast moldova monaco nameric namerica netherl nethrlnd newzeal nkorea norway nzealan poland '
        'portuga prcf prtric prtorico romania russia samer sanmar scotland seasia serbia singap skorea slovak sloven spain sweden switz taiwan tajiki thailan turkey turkmen uk ukf ukraine unf usa usaf usamap '
        'uzbeki vatican venez venzla wales world yugof alabama alaska arizona arkansas californ colorado connetic delaware florida hawaii idaho illinois indiana iowa kansas kentucky louisian '
        'maine maryland massachu michigan minnesot misisipi missouri montana nebraska nevada newhamps newyork njersey nmexico ncarolin ndakota ohio oklahoma oregon pennsylv rdisland scarolin '
        'sdakota tennesse texas utah vermont virginia washingt wisconsi wvirgini wyoming 3dusmap showmap mapusa mapworld worldmap flag flg globe geogrphy satltmap ottawa australa')
ARGENT = ('1dollar argpeso astdollr bagomony bpound cadol cash centimes chilpeso cndamoun coin cyppound dankrone deumk deutschm dime dinar dm dollar dolrcent drachma escudo ffran forint franc '
          'frcoins frfranc guild hkdollr iclkrona irpound italcoin koruna krona krone kroon kuna lat lei lek lev lira lire litas markka money nickel nzdollar penny peseta peso pieslice piggy pigbank '
          'poundstr quarter rand real ringgit ruble rupee rupiah sfranc sngdollr swfranc tklira tolar twndollr unavia won yen zloty profit banker banking loss piechart stocktkr mktbear mktbull bolivare potgold')
SUJETS = {
    'fetes': 'bells elfbag elflist elfstar snowman snowhous twobells holihorn welltoon shwrtoon xmas noel santa claus elf mstletoe holly poinset nativ natvty sleigh reindr reindeer rudolph snkntree firtree trimtree stocking wreath wiseman caroler cmastoon halween hauntbkg '
             'trckotrt pumpkin scarecat scary witch ghost goblin grimreap skulgate frnknstn cauldron devilfrk mummy mask eastoon estregs eggfun chickegg skletegg shamrok 4clover 4lfclvr stpatty valhrt valentin '
             'valentn vdaytoon cupid cndyhrt lovebrd luvb thkstoon tkvgtoon turkey pilgrim corncpia cornuco newyear newyr nwyr firewk firewrk firecr sprng spring summer autumn winter maplelf fall dreidel '
             'hanukah menorah shofar kiddush lincoln washngtn presd groundhg octbrfst earthday momsday momtoon dadsday dadtoon hlly seastoon festive parade flgusa bcandl candles candle remembr libertybel lbrtybel',
    'occasions': 'wedbell wedcake wedcple wedfun wedquilt wedring wedshwr hrtbell hrtbnnr hrtdanc hrtleaf hrtmotif hrtstar hrt_leaf giving trophfun bestfrnd holdhand bday birthtoo bdcake bdintoon heart hrt love kiss wed ring justwed gift present bouquet balloon balon bllncrry party prty confeti conftti champgn champgne chmp corkpop bigcake cakehoho '
                 'getwell graduat grad hatgrad diploma certifct baby babyshr babyshw strkbby stork celeb congrat medal trophy 1stplace laward awrd ribbon ribn dimdshdw partinv numone rbnbells rbnornam goodmail',
    'prehistoire': 'brntsaur caveman ptrdct ptroglph t_rex tyranrex dinosaur ptro',
    'oiseaux': 'bird eagle owl dove 2dove duck goose heron canary cocktiel parakeet parrot parrtred partridg penguin peng rooster seagull sparrow swanstra toucan ostrich hmgbird oribird oricrane tbird trkeyfun turkeys',
    'vie-marine': 'fish shark whale dolphin crab lobster starfish starfsh seahors mantaray shell conch hrmitcrb mussels sandollr swordfsh angelfsh aquarium octopus undrwat',
    'insectes-reptiles': 'ant bumblbee butterf btrfy bttrfly butrfly dragnfly housefly grshppr ladybug spider spiweb snail slug snake lizard gecko seaturtl turtle frog insect',
    'animaux': 'bunny catgray catplay dogcool dogrun oridog orihorse chlion doghouse cowskul saddledo moustrp micemaze twomice animal bear beardesk bearnews bearpnt beartray bighorn blackcat blkcat bulldog buffalo calico cat cow collie dachshnd deer dog donkey elephant elephnt elk gazelle gerbil giraffe greyhnd guineapg '
               'hamster hapydog headdonk headele hippo horse horsrac horsridr hound howldog kangroo kitten 2kitties cutecat luckcat lion mnkytree mole mouse mousemsg pegasus pig polrbear poodle '
               'prtyelph rabbit racehrs reindr rhino sheep siamese spaniel squirrel tabby terrier tiger wolf zebra',
    'plantes-fleurs': 'flwer plntcrry acorn bamboo bflower bflowr bgflower bonsai branch btrees cactus cattail evergrn fern flower flwr flowr floral garden grdn jflower leaf leaves lillies mushrm orchid palmtre plant plntpot poinsett reeds rose stump tree treasia treroots tulip vine vines wheat trplntr treplntr pinecone',
    'ciel-espace': 'bsun suncloud sunrise satltrk astron astrnaut atlantis cloud cosmos earth fullmoon moon planet rain rainbow raincld satlite satellit satdish satldish shuttle snowcld snwflk snowflk solrsys spcshtl spcsht space star shtngstr storm sun tornado tropcsun weather tsun tsnowfl forecast skyroket',
    'paysages': 'tpalms well tunnel catwalk beach bmntn bwaves climbhil desert forest genbeach mountain mountns mtnview ocnwave oceanwav palm savanna scn_ shorline swest tropics volcano waterclr niagrafl mntfuji firefrst earthqk',
    'architecture': 'arch basilica bcity bhomes bridge building buildn buildng castle cathedrl church city colsium column crthous ctyscap dietbldg duomomln eiffel eiffl empirest factory gatearch gazebo highrise home '
                    'house kremlin lghthous lghthse library mansion mingtomb nycity nyc notredme obsrvtry oldcity pagoda park parknite pyramid rooftop school schhse schlhse skyscrp stadshus statlib statlibr sphinx '
                    'stonehen stonhnge supcourt taimajal tokyotwr towrpisa uscapito venice washmonu windmil windmils bigben brandenb arcdetri gondolas gratpyrm gratsphi gratwall lincomem mayantem mtrushmo '
                    'redsquar spacndle sydneyoh toronto tpyrmid t_pueblo paris london londbrdg hyglyphs operahse theater washdc twnstore barnsilo tcelt',
    'voyages': 'dock passcntl customs immigrat luggage openroad suitcas travel twotix tropdrnk hotel campsite',
    'cartes-drapeaux': PAYS,
    'finance': ARGENT,
    'corps': 'abdomen arm armlngth body brain ear eye fingerv finger foot hand handsh hndshak hndweigh lungs skelhand skeletn skull teeth tooth bones thumb fistslam openhand footstp handout handtra handgi handrc longhalr pigtails crewcut',
    'sante': 'ambulanc bandage bandaid bloodpsr capsules caduceus dent doctor docbag drugs emergnc eyedrop firstaid hospbed hospita hospital iv medicin medcircl medlogo medstaff mscope needle nurse paramed patient pharm pill poison prescrip radiatn rehab sick stethscp surgeon surgery syringe tablet thermmtr xrayrm wheelchr whelchr hndicap resthndc lifesav temphot tempcold',
    'cuisine': 'cffeecup cofeebr dnrgravy dnrjello dnrplate dnrpotat dnrroll dnrtrky dnrwine ltrscofe apple appl apples artichk avocado bananas barbque bbq beermug berries bfruit bluebrry bread breadveg brocoli cake candybar candycne carrot cereal cheese cheries cherries chescake chili cinnroll citrus cofecup coffee coffpot cookie corn cup cupcoffe dairy dinetabl dnr drink eggplant eggplnt eggs foodbskt foodcn foodcrt foodgrps frtbskt fruitplt fruitslc garlic garnish gbread grape grapefr hamburgr halfcup hotdog hotnspcy icedrink icetreat junkfood kiwi kniffork knife ladle lattecup lemon lunchbox meal menu milk milkeggs msrcup msrspoon mug onion pan pasta peapod pear pepper picnic pie pineapl pineappl pineaple pizza placeset plceset plum pmpknpie popcorn potato radish rollpin saltnppr servehot servfork skillet sodastrw soup spatula strwbry sundae teabag teapot tea4two tomato trktaste waiter whisk wineglas winegls winegrps winelog wtrmelon 6pack bonbon',
    'maison': 'torch filter filters lteswtch switch fence gloveumb binculrs pktknife dirchair bench bathtub blender bottle btlglass btlplstc broom chest cleaner commode dishwash drawers fan iron jacuzzi key lamp lamptall lantern lckddoor lock micrwave ofchair pictable pictrfrm plug radiator rosevase scissors scissrs sewbut sewing sewknit sewneedl sewtapem sewthimb sewthred sewyarn smkpipe toaster trashcan trshcan tv umbrell umbrla urn arch_urn vaccum washer window windw woodstov flashlig pincush hairdryr bowl door shower wshower cigbutt litebulb liteblb lighton',
    'vetements': 'model tricrtop ballcap baghat cwbyboot glasses goggles hatbndna hatcwby hatglove hatjoker hatsptla hatstack hatwzrd shoe sneaker sombrero sweater ties trunk umbr maskfins dressup',
    'bureau': 'bizdeal bizenvlp bizmtg bizshake biztalk bizwalkr confrnce jeffmemo drivtalk techgrp pushboxs replcard puthere support swamped accntant agrmnt binder biz boxmove brefclok brfcsopn briefcas briefcs calc calclatr calcpapr ceo clipbrd copier datntry datentry fax faxmchne fileb filehand fldrlis highlig litepens marker manpapr manwfile meeting notepad office paprclps paprtall papermen paprmen pcnctbl pens planner pushpin pushpns rcptnist secretry splyoffc stapler taperol tbltalk telecon typewrtr woman wmnwcalc manpcwrk manwtblt mantypng manwbprt ofcstuff presntng prtrait marquee mandesk pntout slides labels forecst',
    'informatique': 'bgbutons cdrom cdman chip cmptrtch cmptwrk cmputer comp computr cptrchok disk diskthw floppy flpydsks gamepad ibm_pc insrtdsk keyboard keybrd laptop lsrprnt modem monitor monitors mousepad multimed network notepc pcclone pcmonitr pcoprat pcport pcwkstn printer programr progrmrs robot scanner server tapedriv towerpc trakbal',
    'communication': 'blahblah package markbox moving movetoon discord interrog onahook ansrmach beeper bizphone billbord blimp bnnrplne camcord camera camragls cellphn cellphon cds courier envelop envlop filmreel keyenv magazine mail media megaphn micrphon microph moviemak movies newsdelv newspapr payphone phon photogfr projectr radio reporter signal soundwav speaker spotlght telephon ltrenvlp vidtape videocas walkman boxradio boombox rec_cd rec_head rec_keyb rec_mike airmail airenvlp postwkr handset talk',
    'sciences': 'atom beaker beakrtub bunsen dna flask micrscp molecule oscscope prism radar scients scientst telescp testtube geomtry balance scale scales',
    'metiers': 'barbrshp nursing paramdc shotgive shesays hesays sheperd architct archtect assemblr automech butcher carpentr carpntr cashier chef cmdytrag cnstrwk cnstwrkr conductr condctr constble eltrcian engineer farmer firefit fireman firehose fireengn foreman forstwkr hairdrsr janitor judge linewkrs lmbrjack mechanx miner oilwrkr pilot plumber plumbng policcar policof realtor surveyor teacher trucker welder whrhswkr workers wrkman wrkwman manrun bizrun firetrk',
    'outils': 'axe bolts clamp drafting gate grdntl hammer hwhammr hwnail hwnut hwscrew hwscrwdr hwwrench jackhmr hydraul hydrant ladder lawnmowr pick pitchfrk pliers saw screwdrv tapemeas tool wrench pulley shovel toolbox blueprnt brngear cogs cone stopwatc tracks',
    'industrie': 'backhoe battery bulldoz coal constrct dam elcmeter farm farmanml forklift gasattn gaspump gasnozzl gastatn grbgtrk hay hortcult oildril oildrill oilline oiltank outlcovr powrline recycle scarecrw scrcrow spkplug tractor trctral tractral treefarm windmill cansalum canstin ',
    'sports': 'skicross skidown skier skiing skitrip baskbal baskball exrcbik stretch tugowar strolwlk kidrun kidsrun aerobics archer archery atbat baseb basebal basket bballbat batter biker bikestmp bowarrow bowling boxer boybike bse_bal bskt bsport bulleye bulls canoe cherldr cycle cycling cyclng dart dartthrw diver dogctchr fbal fball footbal football girlbik golf gymnast highjump hkeyply hockey hurdle iceskat jogger jumping karate kayak kickball kicker maskfin rlrsktr rodeo rowmach rugby runner running sailing scubad skat sktbrdng sktebrd ski snorkl snowwalk soccer socrply sport sprint strmach swim tnisply tnnsply tennis tredmil vball vbalply volley walkride waterski weighlft wghtlft wghtmch windsrf windsurf pitcher race_car racecar sportcar',
    'loisirs': 'horsshoe horssho match fortune amuseprk amusprk blocks carousel cards carddlr casino chesplyr circus circtent clown dice dominoes feriswhl funfair game gamebrdr jigsaw juke_box kite magician magic magichat matreshk puzzle rllrcstr sandtoys skiprope teddy tedbear toy toybskt toyhors toysold tops doll dolly playgrnd sailboat salboat kidsplay fortncke',
    'musique-spectacle': 'bmusic mrchbnd m_classc m_countr m_jazz m_modern m_rockrl balerina ballet bassplyr cymbals dance dancer dancing drum drumrol frenchrn gtarply guitar harp jazzgrp karaoke kidmusic lovesong m_ mime music operam operaw opera piano pianplyr rockstar saxophon saxplyr singer stardanc strdanc taikodrm tapdance timpani trmptply trumpet ukulele vaudvll violin violn alto dramamsk drama',
    'arts': 'art artist bearpnt classic clippins colrpail crayon easel oilpntr paint painter palette tcray woodcut clrpencl',
    'education': 'splyschl notes examm book books chalkbd chllkbrd educate kidread lecture letters manbook mansitng reader reading schlbus schoolbs teen womnbook xboxpncl writer writegrp writepen wmanread pencil penpaper quillpen ruler rulers globen globeest globewst scroll read write',
    'histoire': 'armor crown egypt pulpit shpwheel shpwhel sword throne viking vkingship vkngship cannon soldier knight cannon spcoc liberty',
    'religion': 'angel bible cherub cross 3cross crosgrd pulpit',
    'armee': 'bomb destryer dynamite jetfight tank warplan warship toysoldr',
    'societe': 'campaign gavel scales justice lady ladies gent male female',
    'transports': '2drvan ferrymt helicopt policeca wheeling haycart vkgship tugmsg anchor airbl airplan airplane ambuln bicycle bus busmsg bussign cablecar car citybus cruz cycle dbldbus firetruck fireengn helicp jet jetblack jetplane lghtrail limo minibus monorail monrail motorcy motorflg motrhom mtrcycle oldcar pickuptr plane ship sedan steambt stmtrain subway sunjet taxi taxibus towtruck train traincar truck van yacht boat bwc traficop freeways road gondola htballon hibisc',
    'panneaux': 'stop stoplght noentry nopark nosmok nodr nodrink oneway parking restmen restroom restwom resthnd restm yield hazard einbahns entry wrongway infohere infoscrn infrmton nosmokng smoking elevator stairs upstair downstr directin walkhere',
    'fleches': 'arrow bigarrow circarro crosarro bentarw disarro flatarro inarrows mixarro multarro uparrows ptrup pointrt pointsta pointup triangl trivert',
    'symboles': 'spot sensuniq diamond cylinder focus ecf unvrslno splash confarro failure obstacle triumph stabbed onalimb undrthmb hold litpath progres progress bgeo bggeomtc bshape bswirl checkm circlsq curvy dots geom hkgra idea insignia question squigl sqglvrt swirl swoosh yinyang logo cuplogo dishlog dishlogo golflog rooflogo starbig starbrst stardv starzap starsun sunicon sunface medal tjaggy tcelt tdeco tdesgn tmetal ttrngl torn tora 3dsquare checkmrk targ ontarget thinku',
    'bordures': 'bdr bellbrdr brdr borders btrfybdr crackbdr fishbrdr flwrbdr metlbdr mailbrd feedbrd prtybdr readbrdr rpplbrd zbrabrdr spttrhrt hrtcrnrr hrtcnrl foodcn ctrcrnr stcrnr ptrocrnr tcorner',
    'fonds': 'bg bgragged bgripple bgstr bgvines bkgrnd graytorn',
    'lettres': 'a ae b c d e f g h i j k l m n o oe p q r s t u v w x xx y z numone',
    'calendrier': 'alarmclk clock digclock hourglas hrglass hr_glass stopwch stopwtch',
    'fantasy': 'chnsdrgn dragon genie alien wizard unicorn',
    'famille': 'babycry babynbox babyseat bbybot family famil famlydnr child kid kiddi girl girls boy momb mombaby mother parents pacifr pram rattle stroller holdbaby friends couple teens superdad',
    'visages': 'face smile hmm hostile worried yeah',
    'gens': 'womnwltr mannjng mannjngl cowboy tparty mom people person man woman audience crowd bizprsn walker walkers walktalk walking hiker lady shopper grocery shopcart ',
}
# Du plus long au plus court : le début de nom le plus précis l'emporte
STEMS = sorted(((w, r) for r, ws in SUJETS.items() for w in ws.split()), key=lambda x: -len(x[0]))
DEFAUT = {'Scrbeans': 'gens', 'Popular': 'symboles'}


def rubrique(nom, dossier):
    s = re.sub(r'\d+$', '', nom.lower())
    for w, r in STEMS:
        if s == w or (len(w) >= 4 and s.startswith(w)):
            return r
    return DEFAUT.get(dossier, 'divers')


def alleger_office(data):
    """Retire de l'export LibreOffice ce qui ne dessine rien ; renvoie None si le fichier n'est pas lisible."""
    t = nettoyer(data)
    if t is None:
        return None
    rt = ET.fromstring(t)
    for k in ('width', 'height', 'id', 'preserveAspectRatio', 'version', '{http://www.w3.org/XML/1998/namespace}space'):
        rt.attrib.pop(k, None)
    garder = {i.get('{http://www.w3.org/1999/xlink}href', '')[1:] for i in rt.iter() if i.get('{http://www.w3.org/1999/xlink}href')}

    def walk(el):
        for ch in list(el):
            tag = ch.tag.split('}')[-1]
            if tag == 'defs' and ch.get('class') in ('ClipPathGroup', 'TextShapeIndex', 'EmbeddedBulletChars', 'TextEmbeddedBitmaps'):
                el.remove(ch); continue
            if tag == 'clipPath' and (ch.get('id') or '').startswith('presentation_clip'):
                el.remove(ch); continue
            walk(ch)
            if tag == 'g':
                for k in list(ch.attrib):
                    if k in ('class', 'id') or k.startswith('{http://xml.openoffice'):
                        del ch.attrib[k]
                if not len(ch):
                    el.remove(ch)
        for k in list(el.attrib):
            if k == 'id' and el.attrib[k] not in garder and not el.tag.endswith(('clipPath', 'linearGradient', 'radialGradient', 'pattern', 'symbol', 'mask', 'marker')):
                del el.attrib[k]
            elif k == 'class' or k.startswith('{http://xml.openoffice'):
                del el.attrib[k]
            elif k == 'clip-path' and 'presentation_clip' in el.attrib[k]:
                del el.attrib[k]

    # Groupes sans attribut : leurs enfants remontent d'un cran
    def aplatir(el):
        new = []
        for ch in list(el):
            aplatir(ch)
            if ch.tag.endswith('}g') and not ch.attrib:
                new.extend(list(ch))
            else:
                new.append(ch)
        el[:] = new
    walk(rt)
    aplatir(rt)
    return ET.tostring(rt, encoding='unicode').encode()


shutil.rmtree(dst, ignore_errors=True); os.makedirs(dst)
vus, items, ratés, doublons = {}, [], [], 0
for d in sorted(DOSSIERS):  # Office d'abord : Popular et Scrbeans reprennent quelques dessins
    for f in sorted(os.listdir(os.path.join(src, d))):
        if not f.lower().endswith('.svg'):
            continue
        n = f[:-4].lower()
        data = alleger_office(open(os.path.join(src, d, f), 'rb').read())
        if data is None:
            ratés.append(f); continue
        h = hashlib.md5(data).hexdigest()
        if h in vus:  # même dessin dans un autre dossier : le dossier s'ajoute aux mots-clés
            doublons += 1
            it = vus[h]
            it[3] = f'{it[3]} {DOSSIERS[d]}'
            continue
        r = rubrique(n, d)
        os.makedirs(os.path.join(dst, r), exist_ok=True)
        fn = n
        if os.path.exists(os.path.join(dst, r, fn + '.svg')):
            fn = f'{n}-{d.lower()}'
        open(os.path.join(dst, r, fn + '.svg'), 'wb').write(data)
        it = [r, fn, re.sub(r'[_\d]+$', '', n).replace('_', ' ').capitalize() or n, DOSSIERS[d]]
        vus[h] = it
        items.append(it)
# Les mots-clés anglais de la Clip Gallery
CAG = {'Office': 'office.cag', 'Popular': 'pop97.cag', 'Powerpnt': 'powerpnt.cag', 'Scrbeans': 'scrbeans.cag'}
par_nom = {it[1]: it for it in items}
for d, f in CAG.items():
    for nom, kw in cag.lire(os.path.join(sys.argv[2], d, f))[1].values():
        n = nom[:-4].lower()
        it = par_nom.get(f'{n}-{d.lower()}') or par_nom.get(n)
        if it:
            mots = it[3].split()
            it[3] = ' '.join(mots + [w for w in dict.fromkeys(kw.lower().split()) if w not in mots and len(w) > 2])
themes = sorted({it[0] for it in items}, key=SLUGS.index)
tidx = {t: i for i, t in enumerate(themes)}
json.dump({'source': 'Microsoft Clipart Extra, cliparts de Microsoft Office 97 (archive.org/details/mso97clipart), SVG-LibreOffice.zip', 'chemin': 'cliparts/office97/{dossier}/{n}.svg',
           'themes': [[t, NOMS[t]] for t in themes], 'items': [[tidx[it[0]]] + it[1:] for it in items]},
          open(os.path.join(dst, 'catalog.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print('office97', len(items), 'dessins', len(themes), 'thèmes', 'doublons', doublons, 'illisibles', ratés)
print('non classés :', ' '.join(it[1] for it in items if it[0] == 'divers'))
