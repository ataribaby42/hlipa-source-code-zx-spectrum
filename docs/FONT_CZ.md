# Český font hry a jeho úpravy

**Hra používá přímo [src_zx/data/font_cz.bin](../src_zx/data/font_cz.bin).**
Tento soubor upravujte v editoru a po uložení spusťte běžné sestavení.
Sestavení ho neregeneruje z ROM ani nepřepisuje.

[HLIPA_CZ_FONT.bin](../output_zx/HLIPA_CZ_FONT.bin) je výstupní kopie pro stažení.
Oba mají formát čistého binárního souboru
o délce **768 bajtů**, bez hlavičky a bez adresy nahrání. Obsahuje 96 znaků
pro kódy **32–127**, každý jako osm bajtů bitmapy 8 × 8 pixelů. Řádky znaku
jdou shora dolů, nejvyšší bit bajtu je levý pixel.

Základem je standardní font ROM ZX Spectra 48K z adres `$3D00–$3FFF`.
Patnáct pozic tvoří dříve vytvořené české verzálky, ostatních 81 znaků
v dodané výchozí podobě odpovídá ROM. Veškeré bitmapy jsou nyní v BINu.
`src_zx/asm/czech_font.asm` obsahuje pouze mapování kódů pro texty hry.

## Mapování

České verzálky nahrazují 15 původních symbolů podle následující tabulky.
Ď je na pozici 92 (zpětné lomítko), takže znak `%` na pozici 37 zůstává zachovaný.
Kódy odpovídají původním pozicím
ve znakové sadě, nejde o Unicode ani standardní českou kódovou stránku.

| Kód | Hex | Původní znak ZX | Nové písmeno | Offset v BIN |
|---:|---|---|---|---:|
| 35 | `$23` | `#` | Á | 24 |
| 36 | `$24` | `$` | Č | 32 |
| 92 | `$5C` | `\` | Ď | 480 |
| 38 | `$26` | `&` | É | 48 |
| 39 | `$27` | `'` | Ě | 56 |
| 59 | `$3B` | `;` | Í | 216 |
| 64 | `$40` | `@` | Ň | 256 |
| 94 | `$5E` | ↑ | Ó | 496 |
| 95 | `$5F` | `_` | Ř | 504 |
| 96 | `$60` | £ | Š | 512 |
| 123 | `$7B` | `{` | Ť | 728 |
| 124 | `$7C` | svislá čára | Ú | 736 |
| 125 | `$7D` | `}` | Ů | 744 |
| 126 | `$7E` | `~` | Ý | 752 |
| 127 | `$7F` | © | Ž | 760 |

Offset libovolného znaku je `(kód − 32) × 8`. Po převodu do TAP musí mít
datový blok fontu stále délku 768 bajtů; adresa nahrání závisí na použitém
editoru. Soubor neobsahuje menu ikonky ani česká malá písmena.

## Použití při sestavení

Sestavení načítá přesně 768 bajtů zdrojového BINu, jinou délku odmítne.
Font vloží do SNA na `$F400–$F6FF`; do TAP přidá samostatný blok
`HLIPA FONT`, který zavaděč načte na stejné místo. Menu, prohra i výhra
používají tento font z RAM, nikoli bitmapy z ROM. Výherní obrazovka navíc
zobrazuje všech šest sebraných korunek s paprsky.

Závěrečné statistiky používají původní znak `%` na pozici 37.
Ikonky Ploxona a Falmona v menu mají
samostatné bitmapy a kódy `$80–$87`, mimo rozsah fontu.

```text
python -B src_zx/build.py
```

Sestavení také obnoví výstupní kopii `output_zx/HLIPA_CZ_FONT.bin`.
Úpravy proto ukládejte do **src_zx/data/font_cz.bin**, nikoli pouze do výstupní kopie.

Pouze obnovit výstupní kopii bez sestavení hry lze příkazem:

```text
python -B src_zx/tools/export_czech_font.py
```

Tento příkaz pouze zkopíruje zdrojový BIN do výstupu; SkoolKit nepotřebuje.

Regrese `python -B src_zx/tests/font.py` sestaví dočasnou kopii projektu
s upravenými bitmapami H a Í. Ověřuje jejich skutečné vykreslení i s nulovými
bitmapami ROM fontu, zachování upraveného BINu a odmítnutí nesprávné délky.
