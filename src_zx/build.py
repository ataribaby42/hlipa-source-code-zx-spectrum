"""Sestavení samostatné Hlípy pro ZX Spectrum 48K, bez síťového přístupu."""
from pathlib import Path
import hashlib,json,os,re,shutil,struct,subprocess

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'src_zx'
BUILD=SRC/'build'
OUT=ROOT/'output_zx'

def block(flag,data):
    b=bytes([flag])+data
    check=0
    for v in b:check^=v
    return struct.pack('<H',len(b)+1)+b+bytes([check])

def header(kind,name,length,param1,param2):
    return block(0,bytes([kind])+name.encode('ascii').ljust(10,b' ')+struct.pack('<HHH',length,param1,param2))

def number(n):
    return str(n).encode()+b'\x0e\x00\x00'+struct.pack('<H',n)+b'\x00'

def make_tap(code,screen,font,font_address,music,music_address,entry):
    # CLEAR $5FFF chrání BASIC a zásobník ROM před kódem od $6000.
    # Všechny bloky načítá BASIC bez komprese. Oblast ROM 128K na $5B00
    # zůstává nedotčená; IM2 ji obsadí teprve při nativním startu hry.
    # POKE 23739,111 přesměruje výstup kanálu S z $09F4 na RET v $096F,
    # aby názvy dalších bloků nepřepisovaly obrázek. Před USR jej obnovíme.
    lines=[
        b'\xfd '+number(24575)+b':\xe7 '+number(0)+b':\xda '+number(0)
        +b':\xd9 '+number(7)+b':\xdc '+number(1)+b':\xfb',
        b'\xef "OBRAZEK"\xaa',
        b'\xf4 '+number(23739)+b','+number(111),
        b'\xef "HLIPA"\xaf '+number(24576)+b','+number(len(code)),
        b'\xef "HLIPA FONT"\xaf '+number(font_address)+b','+number(len(font)),
        b'\xef "HUDBA"\xaf '+number(music_address)+b','+number(len(music)),
        b'\xf4 '+number(23739)+b','+number(244)+b':\xf9 \xc0 '+number(entry),
    ]
    basic=b''.join(struct.pack('>H',i*10)+struct.pack('<H',len(line)+1)+line+b'\r'
                   for i,line in enumerate(lines,1))
    return (header(0,'HLIPA',len(basic),10,len(basic))+block(255,basic)
            +header(3,'OBRAZEK',len(screen),16384,32768)+block(255,screen)
            +header(3,'HLIPA',len(code),24576,32768)+block(255,code)
            +header(3,'HLIPA FONT',len(font),font_address,32768)+block(255,font)
            +header(3,'HUDBA',len(music),music_address,32768)+block(255,music))

def make_sna(image,entry):
    ram=bytearray(49152)
    ram[0x1b00:0x1b00+len(image)]=image
    ram[0xbfee:0xbff0]=struct.pack('<H',entry)
    h=bytearray(27)
    h[0]=0xfe
    h[23:25]=struct.pack('<H',0xffee)
    h[25]=2
    return bytes(h)+ram

def build():
    BUILD.mkdir(parents=True,exist_ok=True);OUT.mkdir(exist_ok=True)
    font=(SRC/'data/font_cz.bin').read_bytes()
    if len(font)!=768:raise SystemExit('Font src_zx/data/font_cz.bin musí mít přesně 768 bajtů.')
    assembler=os.environ.get('Z80ASM') or shutil.which('z80asm') or shutil.which('z88dk-z80asm')
    if not assembler:raise SystemExit('Chybí z88dk-z80asm. Nainstalujte z88dk a přidejte bin do PATH, nebo nastavte Z80ASM.')
    subprocess.run([assembler,'-b','-m','-Isrc_zx/asm','-Osrc_zx/build','-oHLIPA.bin','src_zx/asm/main.asm'],check=True,cwd=ROOT)
    image=(BUILD/'HLIPA.bin').read_bytes()
    assert len(image)==0xa4f0, f'Neočekávaná délka obrazu: {len(image)}'
    labels={m[1]:int(m[2],16) for m in re.finditer(r'^(\w+)\s+= \$([0-9A-F]+)',(BUILD/'HLIPA.map').read_text(),re.M)}
    entry=labels['zx_boot']
    assert labels['pmd_image_end']==entry
    assert 0x6000<labels['pmd_code_start']<labels['pmd_code_end']<entry
    assert labels['zx_irq']==0x5b5b
    assert labels['zx_font']==0xf400 and labels['zx_font_end']-labels['zx_font']==768
    assert image[labels['zx_font']-0x5b00:labels['zx_font_end']-0x5b00]==font
    assert labels['zx_native_end']<=0xc59d, 'Kód zasahuje do pracovních masek.'
    assert labels['zx_music_start']==labels['zx_font_end']==0xf700
    assert labels['zx_music_start']<labels['zx_music_end']<=0xfe00, 'Hudba zasahuje do IM2.'
    music=image[labels['zx_music_start']-0x5b00:labels['zx_music_end']-0x5b00]
    assert image[0xa300:0xa401]==b'\x5b'*257
    screen=(SRC/'data/loading.scr').read_bytes()
    assert len(screen)==6912
    code=image[0x500:labels['zx_native_end']-0x5b00]
    for ext,data in [('tap',make_tap(code,screen,font,labels['zx_font'],music,labels['zx_music_start'],entry)),
                     ('sna',make_sna(image,entry))]:
        (OUT/f'HLIPA.{ext}').write_bytes(data)
    (OUT/'HLIPA_CZ_FONT.bin').write_bytes(font)
    report={'entry':entry,'load_address':0x6000,'ram_top':0xffff,'machine':'ZX Spectrum 48K',
        'image_bytes':len(image),'tape_code_bytes':len(code),
        'code_end':labels['zx_native_end'],
        'free_regions':[{'start':labels['zx_native_end'],'end_exclusive':0xc59d,
                         'bytes':0xc59d-labels['zx_native_end']},
                        {'start':labels['zx_music_end'],'end_exclusive':0xfe00,
                         'bytes':0xfe00-labels['zx_music_end']}],
        'music_address':labels['zx_music_start'],'music_bytes':len(music),
        'music_player_bytes':labels['zx_music_code_end']-labels['zx_music_start'],
        'music_data_bytes':labels['zx_music_data_end']-labels['zx_music_code_end'],
        'music_work_bytes':labels['zx_music_end']-labels['zx_music_data_end'],
        'font_address':labels['zx_font'],'font_bytes':len(font),
        'font_sha256':hashlib.sha256(font).hexdigest(),
        'loading_screen_bytes':len(screen),'tape_loader':'BASIC','tape_compressed':False,
        'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('HLIPA.*'))}}
    (BUILD/'build-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Hotovo: output_zx/HLIPA.tap a output_zx/HLIPA.sna')
    return report

if __name__=='__main__':build()
