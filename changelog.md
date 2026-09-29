# Historie změn

## v1.3 29. 9. 2026 – anglická varianta

- Běžné sestavení vytváří také `HLIPA_EN.tap` a `HLIPA_EN.sna` s anglickým
  menu, pokyny, statistikami a závěrečnými obrazovkami. Název HLÍPA,
  logo a jména autorů zůstávají původní, stejně jako herní logika a data.
- Přidán anglický překlad příběhu v `story.md`.
- Odstraněny nadbytečné mezery za tokeny a parametry příkazů `LOAD ... CODE`;
  adresy a délky se přebírají z hlaviček páskových bloků.
- Barvy a `FLASH 0` se nastavují před `CLEAR 24575`, které zároveň vyčistí
  obrazovku. Samostatné `CLS` a závěrečné obnovení výstupu ROM nejsou potřeba.
- `POKE 23739,111` potlačí výpis názvů bloků již před načítáním obrázku.
- Bloky se jmenují `HLIPA_PIC`, `HLIPA_FONT` a `HLIPA_MUS`; herní blok
  zůstává `HLIPA`. Sestavení odmítne názvy delší než deset znaků.
- BASIC má 176 bajtů, celý TAP 35521 bajtů. Herní kód a data se nemění.

## v1.2 28. 9. 2026 – načítání z BASICu

- Obrázek, herní kód, font a hudbu načítá přímo BASIC bez komprese.
  Samostatný strojový zavaděč byl odstraněn ze zdrojů i sestavení.
- Názvy bloků nepřepisují úvodní obrázek; před spuštěním hry se obnoví
  standardní výstup BASICu. Herní kód ani data se nemění.
- Ověřeno načítání a následný běh v simulátoru SkoolKit pro 48K a původní
  128K, se zrychleným přenosem i čtením páskových impulzů.

## v1.1 – 25. 9. 2026

- Vítězná obrazovka přehrává hudbu, převod pro beeper
  od Busy soft. Enter nebo nula hudbu ukončí a přejde k nové hře.
- Přehrávač, skladba a pracovní bajty zabírají 1727 bajtů souvisle od `$F700`;
  v tomto bloku zbývá 65 bajtů. Hudbu obsahují TAP i SNA.

## v1.0 – 20. 9. 2026

Prvotní verze
