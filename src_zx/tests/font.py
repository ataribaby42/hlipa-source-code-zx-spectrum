"""Ověří, že úprava BIN projde sestavením a text nepoužívá font z ROM."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from runtime import Machine, ROOT, BUILD


def verify_font():
    original=(ROOT/'src_zx/data/font_cz.bin').read_bytes()
    changed=bytearray(original)
    # Změní H i české Í v názvu hry, aby byly prověřené oba druhy znaků.
    for code in (ord('H'),59):
        changed[(code-32)*8:(code-31)*8]=bytes((0x81,0x42,0x24,0x18,0x18,0x24,0x42,0x81))
    with tempfile.TemporaryDirectory(prefix='font-build-',dir=BUILD) as folder:
        project=Path(folder).resolve()
        assert project.is_relative_to(BUILD.resolve())
        src=project/'src_zx'
        shutil.copytree(ROOT/'src_zx/asm',src/'asm')
        (src/'data').mkdir()
        shutil.copyfile(ROOT/'src_zx/data/loading.scr',src/'data/loading.scr')
        shutil.copyfile(ROOT/'src_zx/build.py',src/'build.py')
        (src/'data/font_cz.bin').write_bytes(changed)
        subprocess.run([sys.executable,'-B',str(src/'build.py')],check=True,capture_output=True)
        assert (src/'data/font_cz.bin').read_bytes()==changed,'Sestavení přepsalo upravený font'
        assert (project/'output_zx/HLIPA_CZ_FONT.bin').read_bytes()==changed
        # Velikost glyphů nemění adresy kódu. Spustí se sestavená upravená binárka.
        m=Machine()
        image=(src/'build/HLIPA.bin').read_bytes()
        m.memory[0x5b00:0x5b00+len(image)]=image
        m.memory[0x3d00:0x4000]=[0]*768  # Z ROM se už žádné písmeno nesmí číst.
        m.run_until(lambda:m.at('zx_menu_wait'))
        base=m.labels['zx_font']
        assert bytes(m.memory[base:base+768])==changed
        # Nadpis HLÍPA je na řádku 1 od sloupce 5.
        for code,col in ((ord('H'),5),(ord('L'),6),(59,7)):
            actual=bytes(m.memory[0x4020+y*256+col] for y in range(8))
            assert actual==changed[(code-32)*8:(code-31)*8],('Font nebyl použit',code)
        (src/'data/font_cz.bin').write_bytes(changed[:-1])
        rejected=subprocess.run([sys.executable,'-B',str(src/'build.py')],capture_output=True)
        assert rejected.returncode!=0,'Sestavení přijalo font o nesprávné délce'
    assert (ROOT/'src_zx/data/font_cz.bin').read_bytes()==original
    report={'edited_bin_used_by_build':True,'rom_font_not_used':True,
            'czech_and_ascii_glyphs_checked':True,'wrong_length_rejected':True}
    (BUILD/'font-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Úprava BIN se projevila ve hře, tisk funguje i bez bitmap fontu v ROM.')


if __name__=='__main__':verify_font()
