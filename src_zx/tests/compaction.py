"""Ověří kompaktní relokaci a průchod hry s vyplněnou volnou pamětí."""
import json
import re
from unittest.mock import patch

from runtime import ROOT, BUILD, symbols
from walkthrough import Player
import replay


def verify_compaction():
    labels=symbols()
    removed=json.loads((ROOT/'src_zx/data/pmd_removed.json').read_text(encoding='utf-8'))
    ranges=[(int(r['pmd_start'],16),int(r['pmd_end_exclusive'],16)) for r in removed]
    assert all(a<b and (i==0 or ranges[i-1][1]<=a) for i,(a,b) in enumerate(ranges))
    checked=0
    for name,address in labels.items():
        match=re.fullmatch(r'pmd_([0-9a-f]{4})',name)
        if not match:continue
        original=int(match[1],16)
        assert not any(a<=original<b for a,b in ranges), name
        expected=0x6000+original-sum(b-a for a,b in ranges if b<=original)
        assert address==expected, (name,hex(address),hex(expected))
        checked+=1
    assert labels['pmd_image_end']==0xc800-sum(b-a for a,b in ranges)
    assert labels['pmd_image_end']==labels['zx_boot']

    regions=[(labels['zx_native_end'],0xc59d),(labels['zx_music_end'],0xfe00)]
    instances=[]

    class GuardedPlayer(Player):
        def __init__(self,contended=False):
            super().__init__(contended)
            self.guards=[]
            for a,b in regions:
                # Pestrý obsah místo nul odhalí závislost na někdejších dírách.
                data=bytes((p^(p>>8)^0xa5)&255 for p in range(a,b))
                self.memory[a:b]=data
                self.guards.append((a,b,data))
            instances.append(self)

        def check_reserves(self):
            for a,b,data in self.guards:
                assert bytes(self.memory[a:b])==data, f'Zápis do rezervy {a:04X}–{b-1:04X}'

        def boot(self):
            super().boot()
            self.check_reserves()

        def frame(self,key=''):
            alive=super().frame(key)
            self.check_reserves()
            return alive

    with patch.object(replay,'Player',GuardedPlayer):
        result=replay.replay(contended=True)
    instances[-1].check_reserves()
    report={'relocated_labels':checked,'removed_pmd_bytes':sum(b-a for a,b in ranges),
            'free_regions':[{'start':a,'end_exclusive':b,'bytes':b-a} for a,b in regions],
            'free_bytes':sum(b-a for a,b in regions),'patterned_ram_survived_walkthrough':True,
            'binary_sha256':result['binary_sha256'],'frames':result['frames']}
    (BUILD/'compaction-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Kompaktní adresy a volná paměť ověřeny:',report['free_bytes'],'bajtů.')


if __name__=='__main__':verify_compaction()
