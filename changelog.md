# Historie změn

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
