"""Ověří vykreslené anglické texty, statistiky a pokračování z poslední korunky."""
import json
from runtime import Machine, ROOT, BUILD
from verify import screen_line
from loading import LoadedMachine
from skoolkit.snapshot import Snapshot


def verify_english():
    m=Machine(variant='HLIPA_EN')
    m.run_until(lambda:m.at('zx_menu_wait'))
    expected={1:'HLÍPA',3:'ATARIBABY 2026',5:'KASUHA SOFTWARE',
              6:'KAREL ŠUHAJDA / TOMÁŠ ŠVEC',8:'DESTROY SIX PLOXONS.',
              10:'AVOID THE FALMONS.',12:'Q  UP-LEFT',13:'A  DOWN-RIGHT',
              14:'O  DOWN-LEFT',15:'P  UP-RIGHT',17:'ALSO CURSOR KEYS 5 6 7 8',
              18:'1 MENU',20:'0 OR ENTER: START',21:'J KEMPSTON: OFF'}
    for row,text in expected.items():
        assert screen_line(m,row,start_col=4 if row in (8,10) else 0)==text,(row,text)
    m.screenshot(BUILD/'zx-menu-en.png')
    m.keys={'J'};m.run_until(lambda:m.at('zx_release'))
    m.keys=set();m.run_until(lambda:m.at('zx_menu_wait'))
    assert screen_line(m,21)=='J KEMPSTON: ON'
    m.keys={'J'};m.run_until(lambda:m.at('zx_release'))
    m.keys=set();m.run_until(lambda:m.at('zx_menu_wait'))
    assert screen_line(m,21)=='J KEMPSTON: OFF'
    ratings=['ABSOLUTELY HOPELESS','VERY POOR','POOR','BELOW AVERAGE',
             'AVERAGE','ABOVE AVERAGE','GOOD','VERY GOOD','EXCELLENT']
    cases=[(n,0,0,0) for n in (0,1,2,4,5,23)]
    cases += [(32,0,0,1),(96,0,0,2),(160,0,0,3),(224,0,0,4),
              (224,1,0,5),(224,3,0,6),(224,7,0,7),(224,15,0,8),
              (256,31,0,8),(10,0,1,8)]
    for visited,mask,special,rating in cases:
        m=Machine(variant='HLIPA_EN')
        m.keys={'0'};m.run_until(lambda:m.at('zx_tick'));m.keys=set()
        for base in (0xf070,0xf0b0):m.memory[base:base+16]=[0]*16
        for room in range(visited):
            m.memory[0xf070+(room//128)*64+(room%128)//8]|=1<<(room%8)
        m.memory[0xf17d]=mask;m.memory[0xf1f3]=special
        m.r[24]=m.labels['zx_game_over']
        m.run_until(lambda:m.at('zx_end_wait'))
        assert screen_line(m,2)=='GAME OVER'
        assert screen_line(m,5)=='HLÍPA HAS VISITED'
        suffix='ROOM' if visited==1 else 'ROOMS'
        assert screen_line(m,6)==f'{visited} {suffix} = {(visited*100+255)//256}%.'
        crowns='NO CROWNS COLLECTED.' if not mask else f'CROWNS COLLECTED: {mask.bit_count()}/6'
        assert screen_line(m,8)==crowns
        assert screen_line(m,11)=='YOUR PERFORMANCE WAS'
        assert screen_line(m,13)==ratings[rating]
        assert screen_line(m,17)=='0 OR ENTER: NEW GAME'
        if visited==23:m.screenshot(BUILD/'zx-game-over-en.png')
    # Načte skutečně distribuovaný snapshot a nechá sběr doběhnout bez kláves.
    path=ROOT/'output_zx/HLIPA_pred_posledni_korunkou_EN.z80'
    m=LoadedMachine(Snapshot.get(str(path)),variant='HLIPA_EN')
    assert m.memory[0xf17d]==31 and m.memory[0xf1f4]==31
    started=m.r[25]
    m.run_until(lambda:m.at('zx_music_key'))
    assert m.memory[0xf17d]==63 and m.memory[0xf1f4]==31
    won={2:'CONGRATULATIONS!',6:'YOUR ADMIRABLE FEAT',7:'WILL BE RECORDED FOREVER',
         8:'IN THE MOLECULAR MEMORY',9:'OF THE ENTIRE HLÍPA NATION',
         10:'AND YOUR BODY WILL BE',11:'POURED, AFTER DEATH, INTO',12:'A CRYSTAL BOTTLE',
         14:'SIX PLOXONS ARE DESTROYED.',16:'0 OR ENTER: NEW GAME'}
    for row,text in won.items():assert screen_line(m,row,3,29)==text,(row,text)
    m.screenshot(BUILD/'zx-victory-en.png')
    m.audio.clear();m.step();m.run_until(lambda:m.at('zx_music_key'))
    assert any(value==16 for _,value in m.audio)
    elapsed=round((m.r[25]-started)/3500000,3)
    m.keys={'E'};m.run_until(lambda:m.at('zx_tick'))
    assert m.memory[0xf17d]==0 and m.memory[0xf1f4]==31
    report={'menu_and_joystick':True,'statistics_cases':len(cases),
            'all_nine_ratings':True,'title_and_author_diacritics':True,
            'last_crown_snapshot':path.name,'snapshot_to_music_seconds':elapsed,
            'victory_text_music_and_restart':True}
    (BUILD/'english-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Anglické texty, statistiky a snapshot před poslední korunkou prošly.')


if __name__=='__main__':verify_english()
