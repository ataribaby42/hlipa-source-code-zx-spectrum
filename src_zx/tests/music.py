"""Porovná celý zvuk s archivem a ověří vítězství, klávesy i testovací snapshot.

Spuštění po sestavení a replay.py --snapshot: python -B src_zx/tests/music.py
Jde o vykonávání Z80 v simulátoru SkoolKit, nikoli poslech na hardwaru.
"""
import hashlib
import json
import os
import shutil
import subprocess
import zipfile

from skoolkit.snapshot import Snapshot
from skoolkit.simutils import from_snapshot
import skoolkit

from runtime import ROOT, BUILD
from walkthrough import Player
from verify import screen_line


def trace_to(m,address,budget=3500000):
    reason,_=m.sim.trace(m.r[24],address,300000000,m.r[25]+budget,
                         True,None,None,None,None,None)
    assert reason==3, ('Nedosažená adresa',hex(address),hex(m.r[24]),reason)


def trace_label(m,label,budget=3500000):
    trace_to(m,m.labels[label],budget)


def verify_original():
    with zipfile.ZipFile(ROOT/'assets/hlipa-hudba-3.zip') as archive:
        original=archive.read('HlipaMusic02.cod')
    # Na původní adrese musí vzniknout přesně původní instrukce a data.
    source=BUILD/'music-reference.asm'
    source.write_text('    org $9000\n    include "music.asm"\n',encoding='utf-8')
    assembler=os.environ.get('Z80ASM') or shutil.which('z80asm') or shutil.which('z88dk-z80asm')
    subprocess.run([assembler,'-b','-Isrc_zx/asm','-Osrc_zx/build',
                    '-omusic-reference.bin','src_zx/build/music-reference.asm'],check=True,cwd=ROOT)
    assert (BUILD/'music-reference.bin').read_bytes()==original+bytes(5)
    reference=Player();native=Player()
    reference.memory[0x9000:0x9000+len(original)+5]=original+bytes(5)
    reference.r[24]=0x9000
    native.r[24]=native.labels['zx_music_start']
    for m in (reference,native):m.r[12]=0xffee
    loop=native.labels['zx_music_init_voices']
    trace_to(reference,loop-0x6700)
    trace_to(native,loop)
    protected=bytes(native.memory[0x4000:0xf700])+bytes(native.memory[native.labels['zx_music_end']:0xff01])
    trace_to(reference,loop-0x6700,2000000000)
    trace_to(native,loop,2000000000)
    assert reference.audio==native.audio, 'Odlišné pulzy nebo časování proti archivu'
    assert reference.r[25]==native.r[25]
    assert len(native.audio)>10000 and any(v==16 for _,v in native.audio)
    assert {p for kind,p in native.ports if kind=='out'}=={254}
    assert {v for _,v in native.audio}=={0,16}
    assert bytes(native.memory[0x4000:0xf700])+bytes(native.memory[native.labels['zx_music_end']:0xff01])==protected
    assert native.r[26]==0, 'Přehrávač povolil IRQ během časování'
    # Začátek dalšího opakování už také vydává zvuk.
    start=len(native.audio)
    trace_label(native,'zx_music_key')
    trace_label(native,'zx_music_key')
    assert any(v==16 for _,v in native.audio[start:])
    return {'original_bytes':len(original),'work_bytes':5,'relocated_bytes':1727,
            'whole_song_identical_port_timing':True,'port_writes':len(reference.audio),
            'song_seconds':round(reference.r[25]/3500000,3),'repeats':True,
            'screen_font_game_and_im2_unchanged':True}


def verify_exit(key,contended):
    m=Player(contended=contended);m.boot()
    m.memory[0xf17d]=63
    m.keys={'O'}
    trace_label(m,'zx_release')
    reason,_=m.sim.trace(m.r[24],m.labels['zx_music_start'],6000000,
                         m.r[25]+3*69888,True,None,None,None,None,None)
    assert reason!=3, 'Hudba přeskočila čekání na uvolnění herní klávesy'
    m.keys=set();trace_label(m,'zx_music_start')
    assert m.memory[m.labels['zx_game_active']]==0
    assert screen_line(m,2,start_col=3,end_col=29)=='BLAHOPŘEJI!'
    screen=bytes(m.memory[0x4000:0x5b00])
    start=len(m.audio)
    trace_label(m,'zx_music_key')
    first_phrase=m.audio[start:]
    # Jiné klávesy ani Kempston vítěznou hudbu neukončí.
    m.keys={'Q','A','O','P','1','J'};m.joystick=31
    before=len(m.audio)
    trace_label(m,'zx_music_key')
    trace_label(m,'zx_music_key')
    assert len(m.audio)>before and bytes(m.memory[0x4000:0x5b00])==screen
    assert m.r[26]==0
    m.keys={key};trace_label(m,'zx_restart')
    assert m.r[26]==1 and m.audio[-1][1]==0
    assert bytes(m.memory[0x4000:0x5b00])==screen
    trace_label(m,'zx_tick',35000000)
    assert m.position()[0]==0 and m.memory[0xf17d]==0 and m.memory[0xf1f4]==31
    m.keys=set();m.memory[0xf17d]=63
    trace_label(m,'zx_music_start')
    start=len(m.audio)
    trace_label(m,'zx_music_key')
    # Opětovné vítězství musí znovu inicializovat samomodifikující přehrávač.
    again=m.audio[start:]
    assert [(t-first_phrase[0][0],v) for t,v in first_phrase]==[(t-again[0][0],v) for t,v in again]
    m.keys={key};trace_label(m,'zx_restart')
    assert m.audio[-1][1]==0
    return {'key':'Enter' if key=='E' else key,'contended':contended,
            'release_wait':True,'other_keys_ignored':True,'screen_unchanged':True,
            'restart':True,'second_victory_reinitializes_music':True}


def verify_snapshot():
    path=ROOT/'output_zx/HLIPA_pred_posledni_korunkou.z80'
    snapshot=Snapshot.get(str(path))
    assert snapshot.machine=='48K'
    m=Player(contended=True)
    m.sim=from_snapshot(skoolkit.CCMIOSimulator,snapshot,
                        config={'fast_djnz':False,'fast_ldir':False})
    m.sim.set_tracer(m);m.memory=m.sim.memory;m.r=m.sim.registers
    assert m.at('zx_tick') and m.memory[0xf17d]==31 and m.memory[0xf1f4]==31
    assert m.position()[0]==171
    # Font a hudba musí pocházet z aktuálního sestavení. Herní kód obsahuje
    # samomodifikující operandy, které už průchod hrou změnil.
    image=(BUILD/'HLIPA.bin').read_bytes()
    a,b=m.labels['zx_font'],m.labels['zx_music_end']
    assert bytes(m.memory[a:b])==image[a-0x5b00:b-0x5b00]
    start=m.r[25]
    m.keys=set();trace_label(m,'zx_release',35000000)
    assert m.memory[0xf17d]==63 and m.memory[0xf1f4]==31
    audio_start=len(m.audio)
    trace_label(m,'zx_music_key')
    trace_label(m,'zx_music_key')
    assert any(v==16 for _,v in m.audio[audio_start:])
    assert any(v==16 for _,v in m.audio)
    return {'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'crowns_before':5,'automatic_last_collection':True,'victory_music':True,
            'seconds_to_music':round((m.r[25]-start)/3500000,3)}


if __name__=='__main__':
    report={'original':verify_original(),
            'exits':[verify_exit(key,contended) for contended in (False,True) for key in ('E','0')],
            'snapshot':verify_snapshot()}
    (BUILD/'music-verification.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Celá skladba odpovídá originálu; Enter, 0, opakované vítězství a snapshot ověřeny.')
