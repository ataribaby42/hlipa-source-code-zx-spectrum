; Samostatný zavaděč nad RAMTOP BASICu ($5EFF), pod hlavním kódem ($6000).
; $5B00–$5BFF zůstává při načítání volné pro systémové rutiny Spectra 128K.
; ROM LD-BYTES načte obrázek, hlavní kód a samostatný 768bajtový font.
; Přímé čtení bloků nekreslí jejich názvy přes obrázek. Konstanty předává build.py.
    org $5f00
tape_start:
    ld ix,$4000
    ld de,6912
    call tape_load_block
tape_load_code:
    ld ix,$6000
    ld de,HLIPA_CODE_BYTES
    call tape_load_block
    ld ix,HLIPA_FONT_ADDRESS
    ld de,768
    call tape_load_block
    jp HLIPA_ENTRY

tape_load_block:
    push ix
    push de
    ld ix,tape_header
    ld de,17
    xor a
    scf
    call $0556
    jr nc,tape_error
    ld a,(tape_header)
    cp 3
    jr nz,tape_error
    pop de
    ld hl,(tape_header+11)
    or a
    sbc hl,de
    jr nz,tape_error
    pop ix
    ld a,$ff
    scf
    call $0556
    jr nc,tape_error
    ret
tape_error:
    rst $08
    defb 26 ; R Tape loading error
tape_header:
    defs 17,0
tape_end:
