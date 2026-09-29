"""Souvislý průchod od startu k výhře; ovládá jen klávesnici.

Nepoužívá checkpointy, hledání cesty ani změny herní paměti.
Spuštění: python -B src_zx/tests/replay.py [--contended] [--snapshot] [--english]
"""
import argparse
import hashlib
import json
from pathlib import Path

from walkthrough import Player, BUILD
from verify import screen_line


def save_last_crown_snapshot(m,english=False):
    """Uloží úplný dosažený stav přibližně sekundu před posledním sběrem."""
    from skoolkit.simutils import get_state
    from skoolkit.snapshot import write_snapshot
    from runtime import ROOT
    suffix='_EN' if english else ''
    path=ROOT/f'output_zx/HLIPA_pred_posledni_korunkou{suffix}.z80'
    m.outfe=m.audio[-1][1] if m.audio else 0
    ram,registers,state,machine=get_state(m.sim)
    write_snapshot(str(path),ram,registers,state,machine)
    m.screenshot(BUILD/f'snapshot-posledni-korunka{suffix}.png')
    return {'file':path.name,'frame':len(m.actions),'position':list(m.position()),
            'crowns_mask':m.memory[0xf17d],'health':m.memory[0xf1f4],
            'instruction':'Nemačkejte pohybové klávesy; poslední sběr a hudba doběhnou asi za sekundu.'}


def replay(contended=False,snapshot=False,english=False):
    record=json.loads((Path(__file__).parent/'data/walkthrough.json').read_text(encoding='utf-8'))
    reference=(BUILD/'HLIPA.bin').read_bytes()
    if hashlib.sha256(reference).hexdigest()!=record['binary_sha256']:
        raise RuntimeError('Záznam patří k jinému sestavení. Po změně hry ověřte a obnovte záznam.')
    variant='HLIPA_EN' if english else 'HLIPA'
    image=(BUILD/f'{variant}.bin').read_bytes()
    digest=hashlib.sha256(image).hexdigest()
    m=Player(contended=contended,variant=variant)
    # Překlad mění nativní texty a jejich adresy, nikoli původní herní logiku.
    assert image[:m.labels['zx_boot']-0x5b00]==reference[:m.labels['zx_boot']-0x5b00]
    m.boot()
    start=m.r[25]
    milestones=[]
    rooms=[m.position()[0]]
    previous_mask=0
    frame=0
    saved_snapshot=None
    for key,count in record['runs']:
        assert key in ('','Q','A','O','P') and count>0
        for _ in range(count):
            frame+=1
            assert m.frame(key), ('Přerušený průchod',frame,m.position(),hex(m.r[24]))
            assert m.memory[0xf1f4]==31, ('Ztráta energie',frame,m.position())
            if snapshot and frame==record['milestones'][-1]['frame']-16:
                assert key=='' and m.memory[0xf17d]==31
                saved_snapshot=save_last_crown_snapshot(m,english=english)
            if m.position()[0]!=rooms[-1]:
                rooms.append(m.position()[0])
            mask=m.memory[0xf17d]
            if mask!=previous_mask:
                milestone={'frame':frame,'room':m.position()[0],
                           'position':list(m.position()[1:4]),'crowns_mask':mask,'health':31}
                milestones.append(milestone)
                print('Korunka',mask.bit_count(),'/ 6, místnost',m.position()[0],flush=True)
                previous_mask=mask
    assert frame==record['frames']
    assert milestones==record['milestones'], ('Odlišné milníky',milestones)
    assert previous_mask==63
    m.keys=set()
    reason,_=m.sim.trace(m.r[24],m.labels['zx_music_start'],6000000,
                         m.r[25]+3500000,True,None,None,None,None,None)
    assert reason==3, ('Nenaběhla závěrečná obrazovka',hex(m.r[24]))
    assert m.memory[m.labels['zx_game_active']]==0
    # Text leží mezi rohovými korunkami; jejich pixely nejsou znaky fontu.
    lines=[screen_line(m,row,start_col=3,end_col=29) for row in range(24)]
    assert ('CONGRATULATIONS!' if english else 'BLAHOPŘEJI!') in lines
    assert ('SIX PLOXONS ARE DESTROYED.' if english else 'ŠEST PLOXONŮ JE ZNIČENO.') in lines
    suffix=('-en' if english else '')+('-contended' if contended else '')
    screenshot=BUILD/f'walkthrough-victory{suffix}.png'
    m.screenshot(screenshot)
    result={'variant':variant,'binary_sha256':digest,'contended':contended,'frames':frame,
            'game_seconds':round((m.r[25]-start)/3500000,3),
            'milestones':milestones,'room_sequence':rooms,'unique_rooms':len(set(rooms)),
            'health':m.memory[0xf1f4],'crowns':6,'victory_screen':True}
    if saved_snapshot:result['snapshot']=saved_snapshot
    (BUILD/f'walkthrough-verification{suffix}.json').write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Výhra ověřena:',frame,'aktualizací,',result['unique_rooms'],'místností,',
          result['game_seconds'],'herních sekund.',flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contended',action='store_true',help='Modelovat čekání CPU na ULA.')
    parser.add_argument('--snapshot',action='store_true',help='Uložit testovací snapshot před poslední korunkou.')
    parser.add_argument('--english',action='store_true',help='Projít anglickou verzi a případně uložit snapshot s příponou _EN.')
    args=parser.parse_args()
    replay(args.contended,args.snapshot,args.english)
