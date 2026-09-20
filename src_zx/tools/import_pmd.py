"""Jednorázová, opakovatelná rekonstrukce PMD podkladu do ASM pro Z80."""
from pathlib import Path
from zipfile import ZipFile
import hashlib, json, re
from skoolkit.traceutils import disassemble

ROOT=Path(__file__).resolve().parents[2]
BUILD=ROOT/'src_zx/build'
ASM=ROOT/'src_zx/asm'

def extract():
    tape=ZipFile(ROOT/'assets/pmd85emu_games_4004-482.zip').read('games-4004-482.ptp')
    pos=0; found=False; blocks=[]
    while pos<len(tape):
        n=int.from_bytes(tape[pos:pos+2],'little');b=tape[pos+2:pos+2+n];pos+=n+2
        if len(b)==63 and b[54:62]==b'HLIPA   ':found=True
        if found:blocks.append(b)
    assert [len(b) for b in blocks]==[63,162,41421]
    t=blocks[2];m=bytearray(65536);p=166
    assert sum(t[:165])%256==t[165]
    while t[p]==255:p+=1
    assert t[p]==0
    p+=1
    while t[p]:
        a=t[p]*256+t[p+1];p+=2
        for y in range(8):m[a+y*64]=t[p];p+=1
    p+=2
    assert p==8525
    a=0
    for i in range(32768):
        m[a]=t[p];p+=1;a=(a*73-1)&32767
        if i%256==255:
            assert sum(t[p-256:p+1])%256==0
            p+=1
    assert p==len(t)
    k=0
    for i in range(32768):k=(k+40)&255;m[i]^=k
    return m

def word(m,a):return m[a]+256*m[a+1]

def pointers(m):
    p={0x2000,0x2002}
    p.update(range(0x2016,0x2816,8))
    p.update(range(0x4100,0x4124,2))
    p.update(range(0x41b0,0x4216,2))
    p.update(range(0x4216,0x42bf,5))
    p.update(range(0x431f,0x432d,5))
    p.update(range(0x4380,0x43c5,4))
    p.update(a for a in range(0x648b,0x6597,2) if word(m,a)>=0x4bca)
    return p

HOOKS={
    0x4d7b:'zx_ret',0x4d60:'zx_ret',0x50f1:'zx_ret',
    0x5284:'zx_tick',0x5e31:'zx_menu',0x5637:'zx_input',
    0x56f1:'zx_present',0x596a:'zx_full_present',0x4f0a:'zx_text',
    0x5f09:'zx_ret',0x4db6:'zx_ret',0x53f9:'zx_ret',
    0x5f6f:'zx_player_dispatch',0x6026:'zx_death',
    0x4ed1:'zx_any_key',0x4ef3:'zx_menu_key',
    0x6315:'zx_player_init',
    0x4c3b:'zx_clear_text',0x4f9e:'zx_home',
    0x6217:'zx_game_over_tick',
    0x59b3:'zx_clear_buffer',
}

def walk(m):
    seeds=[0x58a4,0x566d,0x567f,0x5e65,0x50ed,0x5731,0x573a]
    seeds += [word(m,a) for a in pointers(m) if 0x4bca<=word(m,a)<0x648b]
    seen={};todo=seeds[:]
    while todo:
        pc=todo.pop()
        while 0x4bca<=pc<0x648b and pc not in seen:
            t,n=disassemble(m,pc);seen[pc]=(t,n)
            if pc in HOOKS or pc in (0x4ea9,0x50f0):break
            op=m[pc]
            if t.startswith(('JP ','CALL ')) and '(' not in t:
                dest=word(m,pc+1);todo.append(dest)
            if t.startswith(('JR ','DJNZ ')):
                todo.append((pc+2+(m[pc+1]+128)%256-128)&65535)
            if op in (0xc9,0xc3,0xe9):break
            pc+=n
    return seen

def emit(m,code):
    # Původní adresy zůstávají jako identifikátory; fyzické adresy jsou +$6000.
    reloc={a for a in pointers(m) if word(m,a)<0x8000}
    fake_ld={0x601f,0x606c,0x6096,0x60b5,0x60b8,0x60d7,0x60da,0x6179}
    for a,(t,n) in code.items():
        if a in HOOKS:continue
        if n==3 and '$' in t:
            v=word(m,a+1)
            if t.startswith(('JP ','CALL ')) or ('(' in t and m[a] in (0x22,0x2a,0x32,0x3a)):
                if v<0x8000:reloc.add(a+1)
            elif m[a] in (0x01,0x11,0x21,0x31) and 0x100<=v<=0x8000 and a not in fake_ld:
                reloc.add(a+1)
    patches={a:(f'jp {name}',3) for a,name in HOOKS.items()}
    # Sdílené epilogy, tabulka zrcadlení a adresní rozdíly původního programu.
    patches.update({0x50f0:('pop af',1),0x50f1:('ret',1),0x4ea9:('ret',1),
        0x5542:('ret',1),0x4d26:('ld b,$60',2),
        0x55e7:('ld de,$4530',3),0x6324:('ld de,$3bd2',3),
        0x5f1c:('ld de,$32d8',3),0x5798:('call zx_macro',3),
        0x5d5e:('ld de,$3800',3),0x5eeb:('ld de,$3800',3),
        0x4bf7:('jp zx_mask_sp\n    nop',4),0x4c1f:('jp zx_restore_sp\n    nop',4),
        0x4c6c:('jp zx_sprite_sp\n    nop',4),0x55c1:('jp zx_tile_sp\n    nop',4)})
    out=['; Hlípa: rekonstruovaný PMD kód a data pro ZX Spectrum.',
         '; Adresy v komentářích jsou původní PMD adresy; přesun je +$6000.',
         '; Změny platformy jsou pojmenované skoky do spectrum.asm.',
         '; Běžné sestavení tento soubor NIKDY znovu negeneruje.',
         '; Obraz a masky, všech 256 záznamů místností i herní tabulky zůstávají původní.']
    a=0
    while a<0x6800:
        if a in patches:
            t,n=patches[a];out.append(f'    {t} ; PMD ${a:04X}');a+=n;continue
        if a in code:
            t,n=code[a]
            # Překrývající se instrukce (např. LD HL maskující LD A) jsou úmyslné.
            if a+1 in reloc:t=re.sub(r'\$[0-9A-F]{4}',f'${(word(m,a+1)+0x6000)&65535:04X}',t)
            out.append(f'    {t.lower()} ; PMD ${a:04X}')
            a+=n;continue
        if a in reloc:
            out.append(f'    defw ${(word(m,a)+0x6000)&65535:04X} ; PMD ${a:04X}, ukazatel');a+=2;continue
        start=a;a+=1
        while a<0x6800 and a-start<16 and a not in patches and a not in code and a not in reloc:a+=1
        out.append('    defb '+','.join(f'${b:02X}' for b in m[start:a])+f' ; PMD ${start:04X}')
    out += ['    defs $1800,0 ; pracovní obraz 192 x 192, 6 bodů v bajtu']
    (ASM/'game.asm').write_text('\n'.join(out)+'\n',encoding='utf-8')
    (BUILD/'import-report.json').write_text(json.dumps({'sha256_pmd_ram':hashlib.sha256(m[:32768]).hexdigest(),'instructions':len(code),'relocations':len(reloc),'native_hooks':{f'{a:04X}':n for a,n in HOOKS.items()}},indent=2))

if __name__=='__main__':
    BUILD.mkdir(parents=True,exist_ok=True);ASM.mkdir(parents=True,exist_ok=True)
    m=extract();(BUILD/'original-pmd.bin').write_bytes(m)
    code=walk(m)
    print('instructions',len(code))
    (BUILD/'pointer-candidates.txt').write_text('\n'.join(f'{a:04X} {t}' for a,(t,n) in sorted(code.items()) if re.match(r'LD (HL|DE|BC|SP),\$',t)))
    (BUILD/'code-map.json').write_text(json.dumps(code))
    emit(m,code)
