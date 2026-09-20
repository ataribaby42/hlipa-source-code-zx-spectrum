"""Kopie aktuálního 768bajtového fontu používaného při sestavení hry.

Zdroj src_zx/data/font_cz.bin se nikdy neregeneruje z ROM ani nepřepisuje.
Stejnou výstupní kopii vytváří i běžné sestavení.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def export():
    font = (ROOT / 'src_zx/data/font_cz.bin').read_bytes()
    if len(font) != 768:
        raise ValueError('Font src_zx/data/font_cz.bin musí mít přesně 768 bajtů.')
    output = ROOT / 'output_zx/HLIPA_CZ_FONT.bin'
    output.parent.mkdir(exist_ok=True)
    output.write_bytes(font)
    print(f'Hotovo: {output.name}, {len(font)} bajtů.')
    return output


if __name__ == '__main__':
    export()
