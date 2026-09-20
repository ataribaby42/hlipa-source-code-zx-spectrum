"""Čtyři zkratky z komentářů Herního archeologa, od startu pouze klávesami.

Nepoužívá uložené stavy ani zásahy do herní paměti.
Spuštění: python -B src_zx/tests/shortcuts.py [--contended]
"""
import argparse
import hashlib
import json
from pathlib import Path

from walkthrough import Player, BUILD


def replay(contended=False):
    record=json.loads((Path(__file__).parent/'data/shortcuts.json').read_text(encoding='utf-8'))
    digest=hashlib.sha256((BUILD/'HLIPA.bin').read_bytes()).hexdigest()
    assert digest==record['binary_sha256'],'Záznam je nutné ověřit na novém sestavení.'
    results=[]
    suffix='-contended' if contended else ''
    for case in record['cases']:
        m=Player(contended=contended);m.boot()
        for phase in (record['approach'],case):
            rooms=[m.position()[0]]
            for key,count in phase['runs']:
                assert key in ('','Q','A','O','P') and count>0
                for _ in range(count):
                    assert m.frame(key),(case['name'],len(m.actions),m.position())
                    assert m.memory[0xf1f4]==31,'Průchod ztratil energii.'
                    if m.position()[0]!=rooms[-1]:rooms.append(m.position()[0])
            assert list(m.position())==phase['position'],(case['name'],m.position())
            if phase is record['approach']:
                assert len(m.actions)==phase['frames']
                m.screenshot(BUILD/f'shortcut-wall{suffix}.png')
        assert rooms==case['room_sequence'],(case['name'],rooms)
        assert m.memory[0xf17d]==case['crowns_mask']==13
        assert m.memory[m.labels['zx_game_active']]==1,'Vstup do místnosti nesmí vyhlásit výhru.'
        if case['name']=='podium':
            assert m.cell(7,7,8) and not m.cell(7,7,9),'Hlípa nestojí na stupínku.'
        m.screenshot(BUILD/f"shortcut-{case['name']}{suffix}.png")
        results.append({'name':case['name'],'frames':len(m.actions),'room_sequence':rooms,
                        'position':list(m.position()),'crowns':3,'health':31,'game_active':True})
        print('Zkratka ověřena:',case['name'],m.position(),flush=True)
    (BUILD/f'shortcuts-verification{suffix}.json').write_text(json.dumps({
        'binary_sha256':digest,'contended':contended,'cases':results},indent=2)+'\n',encoding='utf-8')
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contended',action='store_true',help='Modelovat čekání CPU na ULA.')
    replay(parser.parse_args().contended)
