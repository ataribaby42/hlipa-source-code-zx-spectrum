"""Převod dodaného černobílého obrázku do bitmapy a atributů ZX Spectrum.

Spouští se pouze při změně předlohy; běžné sestavení nepotřebuje Pillow.
"""
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]


def make_screen():
    source=Image.open(ROOT/'assets/nahravaci_obrazek.png').convert('L')
    bounds=source.getbbox()
    if bounds is None:
        raise ValueError('Předloha neobsahuje kresbu.')
    art=source.crop(bounds)
    scale=min(256/art.width,192/art.height,1)
    size=(round(art.width*scale),round(art.height*scale))
    art=art.resize(size,Image.Resampling.NEAREST)
    screen=Image.new('L',(256,192),0)
    screen.paste(art,((256-art.width)//2,(192-art.height)//2))
    screen=screen.point(lambda value:255 if value>=128 else 0)
    data=bytearray(6912)
    for y in range(192):
        for x in range(256):
            if screen.getpixel((x,y)):
                address=(y&192)*32+(y&7)*256+(y&56)*4+x//8
                data[address]|=128>>(x&7)
    data[6144:]=bytes([0x47])*768  # BRIGHT 1, bílý inkoust, černý papír.
    folder=ROOT/'src_zx/data'
    folder.mkdir(exist_ok=True)
    (folder/'loading.scr').write_bytes(data)
    screen.resize((768,576),Image.Resampling.NEAREST).save(ROOT/'docs/nahravaci-obrazek-zx.png')
    print('Obrazovka: 256 x 192, kresba:',size,'bajtů:',len(data))


if __name__=='__main__':
    make_screen()
