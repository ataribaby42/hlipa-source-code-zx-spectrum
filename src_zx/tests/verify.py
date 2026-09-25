"""Regrese relokace, původní mapy, rasteru, ovládání a distribučních souborů."""
from runtime import *
import json,hashlib,time,struct
sys.path.insert(0,str(ROOT/'src_zx/tools'))
from import_pmd import extract
from pmd_reference import ram_sim

CZECH_MAPPING=dict(zip((35,36,92,38,39,59,64,94,95,96,123,124,125,126,127),
                       'ÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ'))

def call_zx(m,addr):
    m.r[24]=addr;m.r[6]=addr>>8;m.r[7]=addr&255;m.r[12]=0xffee
    m.memory[0xffee:0xfff0]=[0,0x5b]
    m.run_until(lambda:m.r[24]==0x5b00,600000)

def call_pmd(s,addr):
    r=s.registers;r[24]=addr;r[6]=addr>>8;r[7]=addr&255;r[12]=0xffee
    s.memory[0xffee:0xfff0]=[0,0x80]
    for _ in range(600000):
        if r[24]==0x8000:return
        if not 0x4bca<=r[24]<0x648b:raise AssertionError(f'PMD PC {r[24]:04x}')
        s.run()
    raise AssertionError('PMD limit')

def reference(crowns=False):
    p=list(extract());p[0xe000:0xf400]=[0]*0x1400
    if not crowns:p[0x59d9]=0xc9  # Ukazatele ZX jsou mimo původní hrací plochu.
    for a in [0x4d7b,0x4d60,0x5e31,0x5f09,0x4ea9,0x50f1]:p[a]=0xc9
    p[0x50f0]=0xf1
    p[0x5f6f:0x5f78]=bytes.fromhex('11 ab 64 3a 38 f1 c3 1a 4e')
    p[0xf1f8:0xf1fa]=[0x0e,0x0d]
    p[0xf03a:0xf03c]=[0x34,0x12]
    p[0xff00:0xff02]=[0x4d,0x65]
    return ram_sim(p,registers={'PC':0x58a4,'SP':0xff00})

def ref_frame(s,bits):
    if s.registers[24]==0x5284:s.registers[24]=0x5292
    for _ in range(600000):
        pc=s.registers[24]
        if pc==0x5284:return
        if pc==0x5637:
            s.registers[0]=bits;s.registers[24]=0x566d
        if not 0x4bca<=s.registers[24]<0x648b:raise AssertionError(f'PMD PC {s.registers[24]:04x}')
        s.run()
    raise AssertionError('PMD frame limit')

def start():
    m=Machine();m.keys={'0'}
    m.run_until(lambda:m.r[24]==m.labels['pmd_5332'])
    m.memory[0xf03a:0xf03c]=[0x34,0x12]
    m.keys=set();m.run_until(lambda:m.at('zx_tick'))
    return m

def clean_scene_raster(data):
    data=bytearray(data)
    for cx,cy in CROWN_POSITIONS:
        for y in range(cy,cy+27):
            for x in range(max(32,cx),min(224,cx+24)):
                data[y*24+(x-32)//8]&=255^(128>>(x%8))
    return bytes(data)


def zx_raster(m):
    return clean_scene_raster(bytes(m.memory[0x4000+(y&192)*32+(y&7)*256+(y&56)*4+x] for y in range(192) for x in range(4,28)))

def pmd_raster(p):
    out=bytearray()
    for y in range(192):
        row=0
        for x in range(192):
            row=(row<<1)|((p[0xca08+y*64+x//6]>>(x%6))&1)
        out.extend(row.to_bytes(24,'big'))
    return clean_scene_raster(out)

def differential():
    total=0
    for key,bits in [('',0),('Q',2),('A',1),('O',8),('P',4)]:
        m=start();s=reference();ref_frame(s,0)
        for n in range(18):
            assert bytes(m.memory[0xf135:0xf139])==bytes(s.memory[0xf135:0xf139]),(key,n,'postava')
            assert zx_raster(m)==pmd_raster(s.memory),(key,n,'raster')
            m.keys={key} if key else set()
            m.step();m.run_until(lambda:m.at('zx_tick'))
            ref_frame(s,bits);total+=1
        print('Shoda PMD / ZX, ovladani',key or 'klid',flush=True)
    return total

def all_rooms():
    m=start();s=reference();hashes=[]
    for room in range(256):
        m.memory[0xf1f0]=room;s.memory[0xf1f0]=room
        for addr in (0x5745,0x59b3,0x5909):
            call_zx(m,m.labels[f'pmd_{addr:04x}']);call_pmd(s,addr)
        a=bytes(m.memory[0xc800:0xe000]);b=bytes(s.memory[0x6800:0x8000])
        assert a==b,f'Odlišná geometrie místnosti {room}'
        for row in range(64):
            start_col=0xe030+row*64
            assert m.memory[start_col:start_col+16]==s.memory[start_col:start_col+16],f'Kolize {room}'
        hashes.append(hashlib.sha256(a).hexdigest())
        if room%64==0:print('Shoda mistnosti',room,flush=True)
    return hashes

def packaging():
    b=(ROOT/'output_zx/HLIPA.tap').read_bytes();pos=0;blocks=[]
    while pos<len(b):
        n=int.from_bytes(b[pos:pos+2],'little');t=b[pos+2:pos+2+n];pos+=2+n
        checksum=0
        for v in t:checksum^=v
        assert checksum==0;blocks.append(t)
    assert pos==len(b) and len(blocks)==12
    assert [part[0] for part in blocks]==[0,255]*6
    loader=(BUILD/'tape_loader.bin').read_bytes()
    assert blocks[3][1:-1]==loader
    assert int.from_bytes(blocks[2][14:16],'little')==0x5f00
    assert 0<len(loader)<=256
    assert blocks[5][1:-1]==(ROOT/'src_zx/data/loading.scr').read_bytes()
    assert int.from_bytes(blocks[4][14:16],'little')==0x4000
    # Obrazovka končí před pracovní oblastí ROM 128K na $5B00.
    assert int.from_bytes(blocks[4][12:14],'little')==6912
    assert blocks[7][1:-1]==(BUILD/'HLIPA.bin').read_bytes()[0x500:symbols()['zx_native_end']-0x5b00]
    font=(ROOT/'src_zx/data/font_cz.bin').read_bytes()
    assert len(font)==768 and blocks[9][1:-1]==font
    assert int.from_bytes(blocks[8][12:14],'little')==768
    assert int.from_bytes(blocks[8][14:16],'little')==symbols()['zx_font']
    labels=symbols()
    music=(BUILD/'HLIPA.bin').read_bytes()[labels['zx_music_start']-0x5b00:labels['zx_music_end']-0x5b00]
    assert blocks[11][1:-1]==music
    assert int.from_bytes(blocks[10][12:14],'little')==len(music)
    assert int.from_bytes(blocks[10][14:16],'little')==labels['zx_music_start']
    assert (ROOT/'output_zx/HLIPA_CZ_FONT.bin').read_bytes()==font
    sna=(ROOT/'output_zx/HLIPA.sna').read_bytes()
    assert len(sna)==49179 and sna[25]==2
    offset=27+symbols()['zx_font']-0x4000
    assert sna[offset:offset+768]==font
    offset=27+labels['zx_music_start']-0x4000
    assert sna[offset:offset+len(music)]==music
    sp=int.from_bytes(sna[23:25],'little')
    assert int.from_bytes(sna[27+sp-16384:29+sp-16384],'little')==symbols()['zx_boot']

def controls_and_lifecycle():
    outcomes={}
    for key in ('Q','A','O','P','7','6','5','8'):
        m=start();m.keys={key};m.run_until(lambda:m.steps()>=13)
        outcomes[key]=m.position()
    for key,arrow,joy,xy in [('Q','7',8,(3,4)),('A','6',4,(3,1)),
                             ('O','5',2,(1,3)),('P','8',1,(4,3))]:
        m=start();m.memory[m.labels['zx_kempston']]=1
        m.joystick=joy;m.run_until(lambda:m.steps()>=13)
        assert m.position()==outcomes[key]==outcomes[arrow],key
        assert m.position()[1:3]==xy,('Nesprávný směr pohybu',key,m.position())
    # Bez zvoleného rozhraní se floating bus nesmí vykládat jako pohyb.
    m=start();m.joystick=15;m.run_until(lambda:m.steps()>=13)
    assert not m.ports[('in',31)]
    m=Machine();m.run_until(lambda:m.at('zx_menu_wait'))
    m.screenshot(BUILD/'zx-menu.png')
    assert screen_line(m,1)=='HLÍPA'
    assert screen_line(m,3)=='ATARIBABY 2026'
    assert screen_line(m,6)=='KAREL ŠUHAJDA / TOMÁŠ ŠVEC'
    assert screen_line(m,8,start_col=4)=='ZNIČ ŠEST PLOXONŮ.'
    assert screen_line(m,10,start_col=4)=='VYHÝBEJ SE FALMONŮM.'
    for row,text in enumerate(('Q  VLEVO NAHORU','A  VPRAVO DOLŮ',
                               'O  VLEVO DOLŮ','P  VPRAVO NAHORU'),12):
        assert screen_line(m,row)==text,('Popisek ovládání',row,screen_line(m,row))
    assert screen_line(m,18)=='1 MENU'
    m.keys={'J'};m.run_until(lambda:m.at('zx_release'))
    m.keys=set();m.run_until(lambda:m.at('zx_menu_wait'))
    assert m.memory[m.labels['zx_kempston']]==1
    m.keys={'0'};m.run_until(lambda:m.at('zx_tick'))
    m=start();immutable=bytes(m.memory[0x6000:m.labels['pmd_image_end']])
    m.keys={'1'};m.run_until(lambda:m.at('zx_menu_wait'))
    m.keys={'E'};m.run_until(lambda:m.at('zx_tick'))
    assert m.memory[0xf1f0]==0 and m.memory[0xf17d]==0
    m.keys=set()
    # Přirozená smrt při pohybu směrem k nepříteli, uvolnění a nová hra.
    m.keys={'A'};m.run_until(lambda:m.at('zx_release'),12000000)
    m.keys=set();m.run_until(lambda:m.at('zx_end_wait'))
    assert screen_line(m,2)=='KONEC HRY',screen_line(m,2)
    assert screen_line(m,13)=='NAPROSTO NEMOŽNÝ',screen_line(m,13)
    assert screen_line(m,17)=='0 NEBO ENTER: NOVÁ HRA',screen_line(m,17)
    m.screenshot(BUILD/'zx-game-over.png')
    m.keys={'0'};m.run_until(lambda:m.at('zx_menu_wait'))
    m.run_until(lambda:m.at('zx_tick'))
    assert bytes(m.memory[0x6000:m.labels['pmd_image_end']])==immutable
    # Cílová obrazovka: nastaví se pouze doložený bitový stav šesti cílů.
    m.keys=set();m.memory[0xf17d]=63
    m.step();m.run_until(lambda:m.at('zx_music_start'))
    m.screenshot(BUILD/'zx-victory.png')
    assert set(p for kind,p in m.ports if kind=='out')=={254}
    assert all(value in (0,16) for _,value in m.audio), 'Zvuk mění černý okraj.'
    return outcomes

def movement_sound():
    from walkthrough import Player
    moves=quiet=turns=0
    durations=[]
    # Čas změny směru prochází všemi fázemi kroku, včetně rychlého L.
    for joystick in (False,True):
        for first,second in [('Q','O'),('O','Q'),('Q','P'),('P','Q'),
                             ('A','O'),('O','A'),('A','P'),('P','A')]:
            for held in range(1,13):
                m=Player()
                if joystick:
                    m.keys={'J'}
                    reason,_=m.sim.trace(m.r[24],m.labels['zx_release'],6000000,
                        m.r[25]+35000000,True,None,None,None,None,None)
                    assert reason==3
                    m.keys=set()
                    reason,_=m.sim.trace(m.r[24],m.labels['zx_menu_wait'],6000000,
                        m.r[25]+3500000,True,None,None,None,None,None)
                    assert reason==3 and m.memory[m.labels['zx_kempston']]==1
                m.boot();settled=m.position()[:4];last_tone=-100
                for frame,key in enumerate(['']*12+[first]*held+[second]*18+['']*12):
                    pos=m.position()
                    if not m.memory[0xf1f4]:break
                    expected=pos[-1]==1 and pos[:4]!=settled
                    if pos[-1]==1:settled=pos[:4]
                    m.audio.clear()
                    if joystick:m.joystick={'':0,'Q':8,'A':4,'O':2,'P':1}[key]
                    alive=m.frame('' if joystick else key)
                    values=[v for _,v in m.audio]
                    assert bool(values)==expected,(joystick,first,second,held,frame,pos,values)
                    if values:
                        assert values==[16,0]*6+[0]
                        assert frame-last_tone>=5,('Dvojité pípnutí při zatočení',first,second,held,frame)
                        last_tone=frame
                        durations.append((m.audio[-1][0]-m.audio[0][0])/3500)
                        moves+=1
                    else:quiet+=1
                    if not alive:break
                turns+=1
    assert all(1.4<=duration<=1.8 for duration in durations)
    return {'turn_cases_keyboard_and_kempston':turns,'completed_steps_with_sound':moves,
            'silent_updates':quiet,'tone_duration_ms_min':round(min(durations),3),
            'tone_duration_ms_max':round(max(durations),3)}


def room_transition_sound():
    from walkthrough import Player
    record=json.loads((ROOT/'src_zx/tests/data/walkthrough.json').read_text(encoding='utf-8'))
    m=Player();m.boot();previous=None;previous_key='';pending=None
    transitions=0;held_directions=Counter();first_steps=Counter()
    for key,count in record['runs']:
        for _ in range(count):
            position=m.position()
            m.audio.clear()
            assert m.frame(key),'Průchod se přerušil při přechodech místností'
            values=[value for _,value in m.audio]
            if previous and position[0]!=previous[0]:
                assert not values,('Pípnutí při samotném vykreslení nové místnosti',previous,position)
                transitions+=1;pending=None
                # Vodorovný průchod při nepřerušeném držení směru.
                if key in 'QAOP' and key and key==previous_key and position[-1]==previous[-1]==1:
                    if position[3]==previous[3] and position[1:3]!=previous[1:3]:
                        held_directions[key]+=1
                        pending=(position[:4],key)
            elif pending:
                origin,direction=pending
                if key!=direction or position[-1]==0x3e:
                    pending=None
                elif position[-1]==1 and position[:4]!=origin:
                    assert values==[16,0]*6+[0],('Chybí první krok uvnitř místnosti',direction,position)
                    first_steps[direction]+=1;pending=None
                else:
                    assert not values,('Opakované pípnutí na okraji nové místnosti',position)
            previous=position;previous_key=key
    assert all(held_directions[key]>0 and first_steps[key]>0 for key in 'QAOP')
    return {'silent_room_arrivals':transitions,'held_direction_crossings':dict(held_directions),
            'first_steps_inside_with_one_tone':dict(first_steps)}

def falling_sound():
    from walkthrough import Player
    # Celá ověřená cesta obsahuje krátké i dlouhé pády, spodní východy a kanál.
    record=json.loads((ROOT/'src_zx/tests/data/walkthrough.json').read_text(encoding='utf-8'))
    m=Player();m.boot();previous=None
    falling=landings=room_crossings=channel_landings=0
    for key,count in record['runs']:
        for _ in range(count):
            position=m.position()
            room,x,y,z,state=position
            support=m.cell(x,y,z-1)
            m.audio.clear()
            assert m.frame(key),'Průchod se přerušil během zvukové zkoušky'
            values=[value for _,value in m.audio]
            if state==0x3e:
                assert not values,('Zvuk během pádu',position,values)
                falling+=1
                if previous and previous[-1]==0x3e and previous[0]!=room:room_crossings+=1
            elif previous and previous[-1]==0x3e:
                assert support and state in (0x3f,0x46),('Chybí podlaha při dopadu',position)
                assert values==[16,0]*6+[0],('Dopad nemá právě jeden tón',position,values)
                landings+=1
                channel_landings+=state==0x46
            elif previous and previous[:4]==position[:4] and state!=1:
                assert not values,('Opakovaný tón bez pohybu',position,values)
            previous=position
    assert landings==27 and room_crossings>=3 and channel_landings==1
    return {'silent_falling_updates':falling,'landings_with_one_tone':landings,
            'silent_room_crossings':room_crossings,'landings_on_channel':channel_landings}

def death_sound():
    from statistics import median
    # Přirozená smrt kontaktem s nepřítelem, bez zásahu do energie nebo PC.
    m=start();m.keys={'A'}
    m.run_until(lambda:m.at('zx_game_over_tick'),12000000)
    # Stav $50 už nemá sprite. $F1F5 je dodatečná prodleva, ne délka animace.
    assert m.memory[0xf138]==0x50 and m.memory[0xa32d+0x50]==0
    finished_at=m.r[25];finished_step=m.steps()
    enemy=bytes(m.memory[0xf139:0xf140])
    m.audio.clear()
    m.run_until(lambda:m.at('zx_death_sound'))
    assert m.steps()==finished_step,'Po smrtelné animaci dál běží herní kroky'
    assert bytes(m.memory[0xf139:0xf140])==enemy,'Falmon se po smrtelné animaci dál pohybuje'
    delay_ms=(m.r[25]-finished_at)/3500
    assert delay_ms<20,('Prodleva po smrtelné animaci v ms',delay_ms)
    assert m.memory[0xf1ba]==0,'Poslední snímek animace čeká na vykreslení'
    # Dokončený herní obraz musí být na obrazovce ještě během výkřiku.
    expected=bytearray()
    for y in range(192):
        row=0
        for x in range(192):
            row=(row<<1)|((m.memory[0xc800+y*32+x//6]>>(x%6))&1)
        expected.extend(row.to_bytes(24,'big'))
    assert zx_raster(m)==clean_scene_raster(expected),'Výkřik není nad dokončeným herním obrazem'
    scene=bytes(m.memory[0x4000:0x5b00])
    m.run_until(lambda:m.at('zx_cls'))
    assert bytes(m.memory[0x4000:0x5b00])==scene,'Herní obraz zmizel před koncem výkřiku'
    m.run_until(lambda:m.at('zx_release'))
    values=[value for _,value in m.audio]
    assert len(values)>256 and set(values)=={0,16},'Chybí výkřik nebo se mění okraj'
    assert values[-1]==0,'Beeper zůstal zapnutý'
    assert all(a!=b for a,b in zip(values[:-2],values[1:-1])),'Nepravidelné přepínání beeperu'
    duration=(m.audio[-1][0]-m.audio[0][0])/3500
    assert 100<=duration<=200,('Délka výkřiku v ms',duration)
    gaps=[b[0]-a[0] for a,b in zip(m.audio[:-2],m.audio[1:-1])]
    assert min(gaps)<median(gaps[:32])*0.75,'Chybí náběh do výšky'
    assert median(gaps[-32:])>median(gaps[:32])*2,'Chybí pokles tónu'
    writes=len(m.audio)
    # Držená klávesa na konci ani čekání bez kláves výkřik neopakují.
    until=m.r[25]+m.frame_duration*6
    m.run_until(lambda:m.r[25]>=until)
    m.keys=set();m.run_until(lambda:m.at('zx_end_wait'))
    until=m.r[25]+m.frame_duration*6
    m.run_until(lambda:m.r[25]>=until)
    assert len(m.audio)==writes,'Výkřik se opakuje na koncové obrazovce'
    assert screen_line(m,2)=='KONEC HRY'
    return {'natural_death_scream_ms':round(duration,3),'port_writes':writes,
            'rising_then_falling_pitch':True,'end_screen_silent':True,
            'after_death_animation_on_game_screen':True,
            'delay_after_animation_ms':round(delay_ms,3),'extra_game_updates_after_animation':0}

def timing():
    m=Machine(contended=True);m.keys={'0'};m.run_until(lambda:m.at('zx_tick'));m.keys=set()
    m.run_until(lambda:m.steps()>=5)
    start_time=m.r[25];start_step=m.steps()
    m.run_until(lambda:m.steps()>=55,10000000)
    elapsed=m.r[25]-start_time
    ms=elapsed*1000/3500000/(m.steps()-start_step)
    assert 55<=ms<=80,ms
    m.screenshot(BUILD/'zx-game-final.png')
    return {'tstates_50_steps':elapsed,'mean_step_ms_with_contention':round(ms,3)}

def teleports_and_ploxons():
    m=start();count=0
    # Spustí skutečnou obsluhu všech přenosů, včetně přenosu do stejné místnosti.
    for p in range(0x9f5c,0xa03d,5):
        room,xy,z,dest,uv=m.memory[p:p+5]
        m.memory[0xf1f0]=room
        m.memory[0xf135:0xf139]=[xy>>4,xy&15,z&15,0x43]
        call_zx(m,m.labels['pmd_6131'])
        assert m.position()[:4]==(dest,uv>>4,uv&15,z>>4),(p,m.position())
        count+=1
    m=start();rooms=[]
    # Umístění pod každého Ploxona; sběr i výsledné vítězství provede herní kód.
    # Jde o cílený test mechanismu, nikoli průchod celé mapy od startu.
    for n in range(6):
        room,xy,z=m.memory[0x8004+n*3:0x8007+n*3]
        rooms.append(room)
        m.memory[0xf1f0]=room
        m.memory[0xf135:0xf139]=[xy>>4,xy&15,z-1,0x43]
        m.memory[0xf1f4]=31;m.memory[0xf1bf]=15
        script=m.labels['pmd_6557']
        m.memory[0xffee:0xfff0]=[script&255,script>>8]
        m.r[12]=0xffee;m.r[24]=m.labels['pmd_58a4']
        m.run_until(lambda:m.at('zx_tick'))
        m.step();m.run_until(lambda:m.memory[0xf17d]&(1<<n),5000000)
        if n==0:
            m.run_until(lambda:m.at('zx_tick'))
            m.step();m.run_until(lambda:m.at('zx_tick'))
            m.screenshot(BUILD/'zx-crown.png')
    m.run_until(lambda:m.at('zx_music_start'))
    assert m.memory[0xf17d]==63
    return {'teleports':count,'ploxon_rooms':rooms,'victory_after_six_contacts':True}

CROWN_POSITIONS=[(24,165),(0,153),(208,165),(232,153),(0,0),(232,0)]


def screen_pixels(m):
    return {(x,y) for y in range(192) for x in range(256)
            if m.memory[0x4000+(y&192)*32+(y&7)*256+(y&56)*4+x//8]&(128>>(x%8))}


def crown_indicators():
    m=start();s=reference(crowns=True);states=[0,1,2,4,8,16,32,63]
    for state in states:
        m.memory[0xf17d]=state;s.memory[0xf17d]=state
        # Prázdný buffer izoluje ikonky od geometrie místnosti.
        call_zx(m,m.labels['zx_cls']);call_zx(m,m.labels['pmd_59b3']);call_pmd(s,0x59b3)
        call_zx(m,m.labels['pmd_59d9']);call_pmd(s,0x59d9)
        assert not any(m.memory[0xc800:0xe000]),'Ukazatele zasáhly do herního bufferu'
        call_zx(m,m.labels['pmd_596a'])
        expected=set()
        for bit,(nx,ny) in enumerate(CROWN_POSITIONS):
            old=s.memory[0x4118+bit*2]+256*s.memory[0x4119+bit*2]
            for y in range(27):
                for x in range(24):
                    if s.memory[old+y*32+x//6]&(1<<(x%6)):
                        expected.add((nx+x,ny+y))
        assert screen_pixels(m)==expected,('Poloha nebo pixely korunek',state,
            len(screen_pixels(m)^expected))
        if state==63:m.screenshot(BUILD/'zx-crowns-all.png')
    return states


def crowns_during_play():
    from walkthrough import Player
    record=json.loads((ROOT/'src_zx/tests/data/walkthrough.json').read_text(encoding='utf-8'))
    m=Player();m.boot();cache={};frames=0
    for key,count in record['runs']:
        for _ in range(count):
            mask=m.memory[0xf17d]
            if mask not in cache:
                expected={}
                for bit,(cx,cy) in enumerate(CROWN_POSITIONS):
                    for y in range(27):
                        for x in range(24):
                            pixel=(m.memory[0xa437+y*4+x//6]>>(x%6))&1
                            if not(mask&(1<<bit)) and not(7<=y<20 and 6<=x<18):pixel=0
                            px,py=cx+x,cy+y
                            addr=0x4000+(py&192)*32+(py&7)*256+(py&56)*4+px//8
                            expected[addr]=expected.get(addr,0)|(pixel<<(7-px%8))
                cache[mask]=expected
            assert all(m.memory[a]==v for a,v in cache[mask].items()),(
                'Přemazané korunky během hry',frames,m.position(),mask)
            assert m.frame(key)
            frames+=1
    return {'frames_with_intact_indicators':frames,'masks':list(cache)}


def screen_line(m,row,start_col=0,end_col=32):
    base=m.labels['zx_font']
    font={bytes(m.memory[base+(c-32)*8:base+(c-31)*8]):chr(c) for c in range(32,128)}
    for code,char in CZECH_MAPPING.items():
        offset=base+(code-32)*8
        font[bytes(m.memory[offset:offset+8])]=char
    line=''
    for x in range(start_col,end_col):
        glyph=bytes(m.memory[0x4000+((row*8)&192)*32+y*256+((row*8)&56)*4+x] for y in range(8))
        line+=font.get(glyph,'?')
    return line.strip()

def game_over_statistics():
    checked=[]
    for visited,mask,special,rating in [(1,0,0,'NAPROSTO NEMOŽNÝ'),(23,0,0,'NAPROSTO NEMOŽNÝ'),
            (2,0,0,'NAPROSTO NEMOŽNÝ'),(4,0,0,'NAPROSTO NEMOŽNÝ'),(5,0,0,'NAPROSTO NEMOŽNÝ'),
            (32,1,0,'ŠPATNÝ'),(96,3,0,'PRŮMĚRNÝ'),(224,31,0,'VYNIKAJÍCÍ'),
            (256,31,0,'VYNIKAJÍCÍ'),(10,0,1,'VYNIKAJÍCÍ')]:
        m=start()
        for base in (0xf070,0xf0b0):m.memory[base:base+16]=[0]*16
        for room in range(visited):
            m.memory[0xf070+(room//128)*64+(room%128)//8]|=1<<(room%8)
        m.memory[0xf17d]=mask;m.memory[0xf1f3]=special
        m.r[24]=m.labels['zx_game_over']
        m.run_until(lambda:m.at('zx_end_wait'))
        percent=(visited*100+255)//256
        suffix='MÍSTNOST' if visited==1 else 'MÍSTNOSTI' if 2<=visited<=4 else 'MÍSTNOSTÍ'
        assert screen_line(m,6)==f'{visited} {suffix} = {percent}%.',screen_line(m,6)
        assert screen_line(m,13)==rating,screen_line(m,13)
        crowns='NENAŠLA ŽÁDNOU KORUNKU.' if mask==0 else f'SEBRANÉ KORUNKY: {mask.bit_count()}/6'
        assert screen_line(m,8)==crowns,screen_line(m,8)
        if visited==23:m.screenshot(BUILD/'zx-game-over-23.png')
        checked.append({'visited':visited,'crowns':mask.bit_count(),'percent':percent,'rating':rating})
    return checked

if __name__=='__main__':
    started=time.time();packaging()
    report={'differential_frames':differential(),'room_hashes':all_rooms(),
            'controls':controls_and_lifecycle(),'movement_sound':movement_sound(),
            'room_transition_sound':room_transition_sound(),'falling_sound':falling_sound(),
            'death_sound':death_sound(),'timing':timing(),
            'teleports_and_ploxons':teleports_and_ploxons(),
            'crown_indicator_states':crown_indicators(),
            'crowns_during_play':crowns_during_play(),
            'game_over_statistics':game_over_statistics()}
    report['seconds']=round(time.time()-started,2)
    (BUILD/'verification.json').write_text(json.dumps(report,indent=2))
    print('Všechny kontroly prošly.',report['seconds'],'s')
