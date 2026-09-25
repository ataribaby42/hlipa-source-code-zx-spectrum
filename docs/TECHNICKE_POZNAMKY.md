# Technické poznámky k převodu

## Výchozí verze

Použita je položka HLIPA v `games-4004-482.ptp`, uložená v přiloženém archivu
`assets/pmd85emu_games_4004-482.zip`. PMD 85 používá procesor kompatibilní
s 8080; jeho herní kód lze po úpravě hardwarových závislostí vykonávat na Z80.
Sharp MZ-800 podklady byly také prohlédnuty, ale tato verze z nich nebere mapu.
Nejde o převod Atari ST grafiky na Spectrum.

Ze sousedního projektu Amigy je převzat pracovní přístup: zachovat původní
logiku a data, oddělit závislosti na počítači, ověřovat rozdíly proti originálu
a používat televizní snímky pro časování. Sestavení na projektu Amigy nezávisí.

Importér kontroluje součty bloků PMD pásky, rekonstruuje permutované adresy
`a = (73*a - 1) & 32767` a odstraní XOR vrstvu se sekvencí přírůstků 40.
SHA-256 dekódovaných prvních 32768 bajtů je
`19bec32e779a2635228cf7bdb0695922caf74e3755d4d170a8af3438a5183c48`.
První rekonstrukce rozpoznala 2443 instrukcí a opravila 1020 adresních
operandů/tabulkových ukazatelů. Následná ruční úprava odstranila nepoužívané
PMD rutiny a sesunula zachované části bez mezer. Symboly `pmd_xxxx` i komentáře
`PMD $xxxx` označují původní PMD adresy; skutečné adresy přiděluje assembler.

Přehled odstranění je v `src_zx/data/pmd_removed.json`: 1980 bajtů rutin,
744 bajtů starých textů menu/nastavení/prohry a 611 bajtů výchozího obsahu
pracovních masek a front. Celkem jde o 3335 bajtů původního obrazu. Zachované
části PMD obrazu mají 23289 bajtů; při jednorázovém porovnání se změnilo pouze
1360 bajtů adresních operandů, ostatní zachované bajty zůstaly stejné.

Odstraněny jsou části starého tisku, hodin, budíku, zvuku, PMD vstupů,
zobrazování, nastavení a prohry, které nahrazuje nativní vrstva. Zachovány
jsou společné návratové části, nepřímé vstupy a data odkazovaná herním kódem.
Tři adresní rozdíly odvozující přístup ke stavu hry jsou nyní výrazy se symboly
(`pmd_4cc4`, `pmd_5f1c`, `pmd_5623`), aby fungovaly i po přesunu rutin.

## Paměť

| Adresy | Obsah |
|---|---|
| `$0000–$3FFF` | Standardní ROM; páskový zavaděč |
| `$4000–$5AFF` | Bitmapa a atributy Spectra |
| `$5B00–$5BFF` | Při načítání prostor ROM 128K; za hry obsluha IM2 a nativní proměnné |
| `$5C00–$5EFF` | BASIC, systémové proměnné a zásobník ROM zavaděče |
| `$5F00–$5FFF` | Dočasný zavaděč TAP; hra jej nepotřebuje |
| `$6000–$A8E1` | Grafika, mapa a zachovaná PMD data |
| `$A8E2–$B9E6` | Kompaktní PMD herní kód |
| `$B9E7–$BAF8` | Řídicí tabulky a konstanty |
| `$BAF9–$C4D4` | Nativní obsluha Spectra, texty a ikonky menu |
| `$C4D5–$C59C` | Volná rezerva, 200 bajtů |
| `$C59D–$C7FF` | Pracovní masky a fronty, 611 bajtů |
| `$C800–$DFFF` | Původní pracovní obraz 192 × 192, 6 bodů v bajtu |
| `$E000–$EFFF` | Kolizní prostor; využity zejména konce 64bajtových řádků |
| `$F000–$F3FF` | Původní pracovní proměnné |
| `$F400–$F6FF` | Font `font_cz.bin`, 768 bajtů |
| `$F700–$FDBE` | Vítězná hudba: přehrávač, data a pět pracovních bajtů, celkem 1727 bajtů |
| `$FDBF–$FDFF` | Volná rezerva, 65 bajtů |
| `$FE00–$FF00` | 257 bajtů `$5B`, vektory IM2 na `$5B5B` |
| `$FF01–$FFEF` | Zásobník, počáteční SP `$FFF0` |

TAP má dvanáct bloků: vždy hlavičku a data pro BASIC, samostatný zavaděč,
úvodní obrázek, herní kód, font a hudbu. BASIC nastaví černý okraj a papír, bílý inkoust
a `CLEAR 24319` (`$5EFF`). Na `$5F00` načte 106 bajtů zavaděče a spustí jej.
Ten pomocí ROM `LD-BYTES` (`$0556`) načte přesně 6912 bajtů obrazovky
na `$4000`, potom 25813 bajtů hry na `$6000`, 768 bajtů fontu na `$F400`
a 1727 bajtů hudby na `$F700`.
Teprve pak skočí na `$BAF9`.
U všech čtyř bloků CODE kontroluje součty hlavičky a dat, typ CODE a očekávanou délku;
při chybě vrací ROM hlášení `R Tape loading error`. Přímé volání ROM
nevypisuje názvy bloků přes obrázek.

Původní společný blok obrázku a zavaděče pokračoval za `$5AFF` do bufferu
tiskárny `$5B00`. V režimu 128K tam ale běží systémové rutiny přepínání ROM.
Jejich přepsání způsobovalo reset při návratu z načítání obrázku. Bylo to
reprodukováno načtením předchozího TAPu z menu původního 128K. Oddělené bloky
a přesun zavaděče na `$5F00` udržují tuto oblast během načítání nedotčenou.

Obsluha IM2 se do `$5B5B` instaluje až při nativním startu hry, po dokončení
všech volání ROM zavaděče. Start také vytvoří tabulku IM2 na `$FE00` a vymaže
pracovní masky a fronty od `$C59D`. Tyto pracovní oblasti ani volné rezervy
se z pásky nenačítají. Hra už nepoužívá původní přerušení ROM a sama
nestránkuje RAM ani ROM. BASIC i jeho zásobník jsou pod zavaděčem a hlavní kód
jej při načítání nepřepíše. SNA obsahuje standardních 49152 bajtů RAM
a 27bajtovou hlavičku; spouští hru přímo. Velikost SNA zůstává 49179 bajtů.
Aktuální TAP má 35558 bajtů oproti 48124 bajtům před odstraněním PMD rutin.

Výslovně vyhrazená volná paměť má celkem **265 bajtů** ve dvou oblastech.
Kontrola při souvislém průchodu zapisuje do rezerv odlišný vzor, ověřuje,
že obsah neovlivní výsledek hry, a po každé aktualizaci kontroluje, že se
nezměnil. Oblast `$C59D–$C5FF` není volná: používá ji rutina PMD `$5D34`
pro pracovní masky, přestože leží před začátkem fronty `$C600`.

Předloha `assets/nahravaci_obrazek.png` je zachována beze změn. Převodní
nástroj odstraní černé okolí kresby 262 × 180 bodů, zmenší ji nejbližším
sousedem na 256 × 176 a vystředí do obrazovky 256 × 192. `loading.scr` obsahuje
6144 bajtů v pořadí řádků Spectra a 768 atributů `$47` (jasná bílá na černé).

## Grafika, vstup a čas

Texty používají buňky 8 × 8 bodů. Všech 96 znaků s kódy 32–127 se čte
z upravitelného `src_zx/data/font_cz.bin` v RAM na `$F400–$F6FF`.
Běžné sestavení soubor neregeneruje; kontroluje jeho délku 768 bajtů,
přiloží jej k TAP i SNA a zkopíruje do `output_zx/HLIPA_CZ_FONT.bin`.
Bitmapy ASCII se již za běhu nečtou z ROM.

České verzálky `ÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ` nahrazují vybrané symboly.
`src_zx/asm/czech_font.asm` definuje jejich kódy `CZ_*`, vlastní bitmapy
neobsahuje. Úplné mapování a postup editace jsou v [FONT_CZ.md](FONT_CZ.md).
Ď používá pozici 92 (zpětné lomítko); znak `%` na pozici 37 je zachovaný
a používá se v závěrečných statistikách.

Menu má mimo font osm znaků `$80–$87` z `menu_icons.asm`. Skládají dvě
ikonky 16 × 16 a používají společný kreslič. Ploxon zachovává původní
pixely spritu PMD `$1928`; Falmon ze spritu `$15A8` je zrcadlený a zmenšený.
Nativní blok končí na `$C4D5`, před pracovními maskami zbývá 200 bajtů.
Sestavení hlídá hranici kódu `$C59D`, přesnou délku a umístění fontu
i konec hudby před tabulkou IM2 na `$FE00`.
Původní kódování PMD textů se nadále zpracovává odděleně.

Původní renderer a maskování spritů píší do obrazu `$C800`. Převod čtyř PMD
bajtů se šesti pixely na tři bajty Spectra zachovává všech 24 pixelů; současně
mění pořadí bitů a adresování řádků. Hrací plocha leží na x = 32 až 223.
Při změně místnosti se překreslí vše. Za běhu se převádějí pouze obdélníky
z původní fronty změn, takže není nutné konvertovat 6144 bajtů každý krok.

Některé původní rutiny používají SP k rychlému čtení grafických dat. Jejich
vstupy vypínají přerušení a společný výstup nejprve obnoví skutečný SP.
IRQ ukládá pouze AF a zvyšuje čítač televizních snímků. Hlavní čekání nastavuje
další termín o tři snímky dopředu; při pomalejším výpočtu nevykonává dodatečné
kroky pro dohánění času. Contention a zmeškané IRQ v chráněných grafických
úsecích mohou periodu prodloužit. Uvedených 60,303 ms je měření úvodní místnosti,
nikoli záruka stejné rychlosti v každé části hry.

Klávesnice se čte z ULA `$FE`. Původní herní filtr protichůdných směrů je
zachován. Q/7/páčka nahoru vede vlevo nahoru, A/6/páčka dolů vpravo dolů,
O/5/páčka vlevo vlevo dolů a P/8/páčka vpravo vpravo nahoru.
Mění se pouze převod vstupů na směry původní herní logiky.
Kempston `$1F` se čte jen po zapnutí v menu; horní bity slouží ještě
jako dodatečná kontrola neplatného výsledku.

Po dokončení kroku Hlípy zazní krátký beeperový tón na portu
`$FE`: 12 přepnutí bitu 4 s prodlevou `DJNZ` od 32, přibližně 1,55 ms.
Jde o dřívější krátký efekt smrti, nyní použitý pro kroky a dopady.
Pád (stav `$F138 = $3E`) je tichý i při přechodu do nižší místnosti.
Přechod z pádu do `$3F` (podlaha) nebo `$46` (kanál) spustí právě jeden tón,
i když se při samotném dosednutí už souřadnice nezmění. Chůze porovnává XYZ
a místnost až ve stavu `$01`, tedy po dokončení animace, s poslední dokončenou
polohou. Původní logika mění souřadnice podle směru v různých fázích kroku;
průběžné porovnávání proto při zatočení mohlo pípnout na konci jednoho
a hned na začátku dalšího kroku. Mezifáze už zvuk nespouštějí. Po celkovém vykreslení místnosti `zx_full_present`
zruší platnost předchozí zvukové polohy. První aktualizace pouze uloží novou
polohu a stav; umístění na okraj nové místnosti tak nepřidá tón těsně před
prvním krokem dovnitř. Totéž platí při startu. Další pohyb a dopady zazní
normálně. Černý okraj se nemění a na konci tónu se beeper vypne.

Stav postavy `$50` už nemá sprite: smrtelná animace skončila. Jeho obsluha
`zx_game_over_tick` proto přechází rovnou do `zx_game_over`. Čítač `$F1F5`
není délka animace; původní odpočet přidával až 31 dalších aktualizací hry,
během kterých se Falmon dál pohyboval. Tento odpočet se již neprovádí.
`zx_game_over` dokončí vykreslení posledního herního snímku pomocí `zx_present`.
Nad tímto obrazem se jednou přehraje samostatný výkřik dlouhý přibližně 140 ms.
Tabulka 24 prodlev vytváří rychlý náběh do výšky a chvějivý
pokles; každý úsek má 24 přepnutí beeperu. Zvuk končí vypnutím beeperu,
potom se vykreslí výsledky hry. Vítězství ani čekání na koncové obrazovce
výkřik nespouští. Efekt potřebuje 59 bajtů kódu a dat včetně volání.

## Důležité rozdíly proti původnímu kódu

- Přímé PMD I/O a čekání na jeho časovač nahrazuje `spectrum.asm`.
- Kontrolní součty používané původním programem k odvozování skoků neplatí
  po relokaci. Dispatcher postavy proto používá skutečnou tabulku `pmd_64ab`
  a koncové stavy mají pojmenované nativní obsluhy.
- Volání sdílených částí mapy jsou zabalená do bitového proudu. Přesun cíle
  o `$6000` se proto dělá za běhu v `zx_macro`.
- Uvodní efekt vykreslení spotřeboval 1024 hodnot původního generátoru náhody.
  Nativní převod stejný posun stavu vypočte přímo; nepřátelé tím nezačnou
  jinou sekvenci jen kvůli novému způsobu zobrazení.
- Vítězství se kontroluje přes šest bitů na `$F17D`. Nová textová obrazovka
  obsahuje české blahopřání podle dodaného `vyhra.png` a nahrazuje
  původní závěrečnou prezentaci. Hudbu přehrává převod od Busy soft
  z `hlipa-hudba-3.zip`. Hodiny a budík nejsou převedeny.
- Šest indikátorů kreslí `zx_crowns` přímo do bitmapy Spectra z původních
  PMD dat na `$A437`. PMD vstup `$59D9` se pouze vrací, herní buffer tak
  neobsahuje staré ikonky. Nové souřadnice levého horního rohu včetně paprsků
  jsou v pořadí bitů korunek `(24,165), (0,153), (208,165), (232,153), (0,0), (232,0)`.
  Nesebraná korunka zachovává pouze vnitřních 12 × 13 pixelů původního obrázku.
  `zx_full_present` ukazatele vždy obnoví. Vítězná obrazovka je po vypsání
  textu znovu vykreslí se stavem všech šesti získaných korunek. Po sběru se kreslí až na konci
  `zx_present`, aby stará fronta obdélníků nesmazala nové paprsky. Regrese
  porovnává každý stav s původní PMD grafikou a sleduje ukazatele během
  všech 6267 aktualizací průchodu.
- Konec hry podle `prohra.png` čte původní návštěvní bity v `$F070–$F07F`
  a `$F0B0–$F0BF`. Procento je `ceil(100 * návštěvy / 256)`, stejně jako
  v PMD rutině `$6259`. Slovní hodnocení má devět stupňů; běžný index je
  `min(8, floor((návštěvy + 32) / 64) + korunky)`, s původní výjimkou pro
  nastavený `$F1F3`. Navíc je korektně ošetřen počet 256 místo přetečení
  osmibitového čítače. Počet místností používá odpovídající český tvar:
  1 místnost, 2–4 místnosti, ostatní počty místností.

## Co zkoušky dokládají

`verify.py` porovnává přeložený port s nezávisle načtenou PMD pamětí. Reference
používá stejný Z80 simulátor v režimu RAM i pod `$4000` a vynechává pouze PMD
I/O, časování a ochranné součty. Jde o regresi relokace a nativních zásahů,
ne o nezávislou emulaci všech vlastností procesoru 8080 nebo celého PMD 85.
Původní kód při testu nečte zdroje portu.

Kontroluje se všech 256 obrazů místností a kolizních polí, 90 snímků při
zadaných směrech, mapování kláves a páčky, vypnutí Kempstonu, smrt a restart.
Zvuková regrese ověřuje dokončené kroky a ticho v mezifázích. Testuje
192 případů zatočení do L přes klávesnici a Kempston: osm dvojic směrů
a dvanáct okamžiků změny směru. Tóny nesmějí být těsně za sebou. Ovládání,
menu a nový start mají také vlastní regresi. Při přirozené smrti
ověřuje délku a změnu výšky výkřiku, zachovaný černý okraj, vypnutí beeperu
a ticho při následném čekání. Od první obsluhy koncového stavu `$50` nesmí
proběhnout další herní aktualizace ani se změnit stav Falmona; vykřiknutí
musí začít do 20 ms. Zkouška v první místnosti naměřila 4,612 ms, potřebných
k dokončení obrazu. Ověřuje také shodu obrazovky s dokončeným herním obrazem
při začátku výkřiku a zachování obrazu až do jeho konce.
Celý záznam průchodu ověřuje 104 tichých aktualizací
pádu, včetně tří přechodů mezi místnostmi, a 27 dopadů s jediným tónem
(včetně jednoho dopadu na kanál). Samostatná zvuková regrese ověřuje také
126 příchodů do nových místností bez pípnutí navíc, průchody s drženým směrem
QAOP (včetně 22 přechodů při drženém A) a tóny prvních kroků uvnitř místností.
`font.py` navíc sestaví dočasnou kopii s upravenými bitmapami H a Í,
potom ověří jejich vykreslení s vymazanými bitmapami ROM fontu. Kontroluje,
že sestavení zdrojový BIN nepřepíše a odmítne nesprávnou délku.
Test 45 kanálů spouští skutečnou přenosovou rutinu; test
Ploxonů umístí postavu pod každou korunku a nechá herní logiku provést kontakt.
Takto se prověří i přechod po šestém cíli, nikoli dostupnost všech cílů
při jednom souvislém hraní.

Tu nyní samostatně ověřuje `replay.py`: od vstupu programu provede start
klávesou `0` a přehraje 6267 herních aktualizací podle uloženého záznamu.
Nemění herní paměť ani registry, nenačítá checkpointy a nevolá interní herní
rutiny napřímo. Kontroluje všechny milníky získání korunek, plnou energii
po každé aktualizaci a skutečný text vítězné obrazovky. Průchod uspěl
v C jádře SkoolKitu s contention i bez ní; čas s contention je 428,943 s.
Jde o simulaci vykonávání Z80 s ROM, klávesnicí a přerušením, nikoli test
fyzického stroje nebo samostatného grafického emulátoru.
Záznam je vázán SHA-256 na ověřené sestavení. Metodu hledání a odchylky od
historického návodu popisuje [průchod hrou](PRUCHOD_HROU.md).

`compaction.py` navíc kontroluje nové adresy všech symbolů `pmd_xxxx`
proti přehledu odstraněných úseků, návaznost PMD a nativního bloku a celý
průchod s vyplněnými rezervami. Protokol je `compaction-verification.json`.

`music.py` sestaví aktuální `music.asm` také na původní adrese `$9000`
a porovná všech 1722 bajtů s `HlipaMusic02.cod` z nedotčeného archivu.
Dalších pět pracovních bajtů leželo v originálu až za koncem souboru COD;
v portu se počítají do obsazeného bloku. Přehrávač má 695 bajtů, data 1027.
Syntaxe je upravena pro z88dk, instrukce a hudební data zůstávají stejné.
Při přesunu o `$6700` se zachovává i poloha tabulky not v rámci stránky.
Celá skladba trvá přibližně 149,582 s a má shodných 185087 zápisů na port
`$FE` i jejich T stavy s originálem v simulátoru bez contention.

Po vykreslení vítězství a uvolnění kláves volá hra `zx_music_start`.
Samomodifikující přehrávač běží s DI, opakuje skladbu a snímá bit 0
klávesnicových řádků `$AFFE`: stačí Enter nebo nula. Vrací se s EI,
hra ztiší beeper a provede běžný restart se zásobníkem `$FFF0`.
Hudba nepotřebuje AY ani stránkování. Zkoušky obou kláves s contention
i bez ní kontrolují také nezměněný obraz, ignorování ostatních kláves
a novou inicializaci hudby při opakovaném vítězství. Celý přehrávací cyklus
nesmí změnit herní paměť, font ani tabulku IM2. Protokol je
`src_zx/build/music-verification.json`; nejde o poslech na fyzickém stroji.

Volba `replay.py --snapshot` uloží úplnou RAM a registry po 6251 herních
aktualizacích do `output_zx/HLIPA_pred_posledni_korunkou.z80`. Jde o stav
dosažený klávesami, s pěti korunkami a plnou silou v místnosti 171.
Bez dalšího pohybu následuje poslední sběr za 16 aktualizací, přibližně
sekundu. `music.py` snapshot znovu načte a ověří sběr i zvuk při modelování
contention. Náhled je v `src_zx/build/snapshot-posledni-korunka.png`.

Deset případů prohry ověřuje přímo české znaky vykreslené na obrazovku,
včetně tvarů pro 1, 2, 4 a 5 místností, 23 místností = 9 % podle reference
a hraničního počtu 256 = 100 %. Zvlášť se kontroluje český titul hry,
jména autorů, pokyny v menu a text vítězství při souvislém průchodu.

`loading.py` nechá SkoolKit provést BASIC/ROM načtení výsledného TAP a zastaví
jej po načtení obrázku a na vstupu hry. V obou bodech porovná všech 6912 bajtů
obrazovky s předlohou SCR, černý okraj a po načtení i celý strojový kód hry.
Z takto získané paměti i z distribučního SNA následně běží menu, 50 herních
aktualizací, pohyb postavy a návrat do menu s novým startem. Navíc se ověří
načtený hudební blok, přehrávání při vítězství a další restart. Prošly modely
48K i původní 128K, oba s přímým nahráním bloků i s `--no-fast-load`, která
čte simulované páskové impulzy přes ROM. Varianta `--machine 128` spouští
skutečné 128K ROM, vybere ENTERem úvodní Tape Loader a při dalším běhu
zachovává všech osm stránek RAM, zvolenou ROM i přerušení po 70908 T stavech.
Nesimuluje se pouhé překopírování výsledku do 48K stroje.

SkoolKit může zrychlovat čekací smyčky; nejde o měření času skutečné pásky.
Reset ohlásil uživatel v Spectaculatoru s původním modelem 128K; oprava byla
ověřena v simulaci SkoolKitu, nikoli přímo v Spectaculatoru. Analogový přenos,
modely +2/+3 a fyzický hardware zatím samostatně ověřeny nebyly.

Nástroje: [z88dk](https://github.com/z88dk/z88dk),
[SkoolKit](https://skoolkit.ca/). Původní ověření vzniklo 20. září 2026;
regrese s vítěznou hudbou a testovací snapshot byly ověřeny 25. září 2026.
