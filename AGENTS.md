# Hlípa pro ZX Spectrum 48K

- Dokumentace projektu je v češtině. Veškerou novou i upravovanou dokumentaci piš česky.
- Nevytvářej Git commity ani neprováděj push na GitHub či jiný vzdálený repozitář.
  Commitování a odesílání změn provádí výhradně uživatel.
- Původní soubory v `assets` zachovej beze změn.
- Cílem je standardní ZX Spectrum 48K; nepoužívej stránkování 128K ani AY.
- Aktuální zdroje jsou `src_zx/asm`. Běžné sestavení je nesmí regenerovat.
- `src_zx/tools/import_pmd.py` je jednorázový nástroj rekonstrukce a relokace,
  nikoli náhrada ruční úpravy aktuálního ASM. Jeho opětovné spuštění přepíše game.asm.
- Mezivýsledky a běhové zkoušky patří do `src_zx/build`, distribuce do `output_zx`.
- Odlišuj sestavení, vykonávání Z80 kódu v testovacím simulátoru, úplný emulátor
  počítače a test fyzického hardwaru. Neuváděj neprovedené ověření jako hotové.
- U změn zásobníku zachovej ochranu krátkých grafických úseků před IRQ.
- Sestavení nesmí záviset na sousedním projektu Amigy ani na nekompletních mezivýsledcích.
