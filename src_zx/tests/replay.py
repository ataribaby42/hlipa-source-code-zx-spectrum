"""Souvislý průchod od startu k výhře; ovládá jen klávesnici.

Nepoužívá checkpointy, hledání cesty ani změny herní paměti.
Spuštění: python -B src_zx/tests/replay.py [--contended]
"""
import argparse
import hashlib
import json
from pathlib import Path

from walkthrough import Player, BUILD
from verify import screen_line


def replay(contended=False):
    record=json.loads((Path(__file__).parent/'data/walkthrough.json').read_text(encoding='utf-8'))
    digest=hashlib.sha256((BUILD/'HLIPA.bin').read_bytes()).hexdigest()
    if digest!=record['binary_sha256']:
        raise RuntimeError('Záznam patří k jinému sestavení. Po změně hry ověřte a obnovte záznam.')
    m=Player(contended=contended)
    m.boot()
    start=m.r[25]
    milestones=[]
    rooms=[m.position()[0]]
    previous_mask=0
    frame=0
    for key,count in record['runs']:
        assert key in ('','Q','A','O','P') and count>0
        for _ in range(count):
            frame+=1
            assert m.frame(key), ('Přerušený průchod',frame,m.position(),hex(m.r[24]))
            assert m.memory[0xf1f4]==31, ('Ztráta energie',frame,m.position())
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
    reason,_=m.sim.trace(m.r[24],m.labels['zx_end_wait'],6000000,
                         m.r[25]+3500000,True,None,None,None,None,None)
    assert reason==3, ('Nenaběhla závěrečná obrazovka',hex(m.r[24]))
    assert m.memory[m.labels['zx_game_active']]==0
    # Text leží mezi rohovými korunkami; jejich pixely nejsou znaky fontu.
    lines=[screen_line(m,row,start_col=3,end_col=29) for row in range(24)]
    assert 'BLAHOPŘEJI!' in lines
    assert 'ŠEST PLOXONŮ JE ZNIČENO.' in lines
    suffix='-contended' if contended else ''
    screenshot=BUILD/f'walkthrough-victory{suffix}.png'
    m.screenshot(screenshot)
    result={'binary_sha256':digest,'contended':contended,'frames':frame,
            'game_seconds':round((m.r[25]-start)/3500000,3),
            'milestones':milestones,'room_sequence':rooms,'unique_rooms':len(set(rooms)),
            'health':m.memory[0xf1f4],'crowns':6,'victory_screen':True}
    (BUILD/f'walkthrough-verification{suffix}.json').write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Výhra ověřena:',frame,'aktualizací,',result['unique_rooms'],'místností,',
          result['game_seconds'],'herních sekund.',flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contended',action='store_true',help='Modelovat čekání CPU na ULA.')
    replay(parser.parse_args().contended)
