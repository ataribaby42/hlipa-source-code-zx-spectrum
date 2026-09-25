; Hudba Hlípy z PMD 85, převod na ZX Spectrum: Busy soft, 25. 9. 2026.
; Zdroj: assets/hlipa-hudba-3.zip / HlipaMusic02.a80.
; Přizpůsobena pouze syntaxe z88dk a adresy; instrukce i data zachovány.
; Přehrávač je samomodifikující, běží s DI a mění AF/BC/DE/HL/IX.
; Skladbu opakuje do stisku Enteru nebo 0, vrací se s EI.
; Včetně pěti pracovních bajtů musí celý blok zůstat pod IM2 na $FE00.
zx_music_start:
zx_music_play_music:
    di
    xor a
    out ($fe),a
    ld (zx_music_loc_7A07+1),a
    ld hl,zx_music_var_7F8B
    ld b,$05
zx_music_init1:
    ld (hl),a
    inc hl
    djnz zx_music_init1
zx_music_init_voices:
    ; Začátek skladby a obou seznamů motivů; sem se vrací i opakování.
    ld a, 3
    ld (zx_music_var_7F8B),a
    ld hl, zx_music_voice1_order
    ld (zx_music_loc_786A+1),hl
    ld hl, zx_music_voice2_order
    ld (zx_music_loc_78C9+1),hl
    ld hl, zx_music_note_periods
    ld (zx_music_loc_784E+1),hl
    ld (zx_music_loc_78AD+1),hl
    xor a
    ld (zx_music_loc_7848+1),a
    ld (zx_music_loc_78A7+1),a
    ld (zx_music_var_7F8F),a
    ld bc, $4040
    ld de, $E0E0
zx_music_main_loop:
    ; Dekodér prvního hlasu.
    ld hl, zx_music_var_7F8F
zx_music_loc_7848:
    ld a, 0
    sub (hl)
    jr nz, zx_music_loc_78A4
zx_music_loc_784E:
    ld hl, 0
zx_music_loc_7851:
    ld a, (hl)
    inc hl
    and a
    jp p, zx_music_loc_7888
    inc a
    jr z, zx_music_loc_786A
    inc a
    ld a, (hl)
    inc hl
    jr z, zx_music_loc_7882
    ld (zx_music_var_7F8D),a
    ld (zx_music_loc_7A21+1),a
    jr zx_music_loc_7851
zx_music_loc_786A:
    ld hl, 0
    push de
    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl
    ld (zx_music_loc_786A+1),hl
    ex de,hl
    pop de
    ld a, h
    or l
    jr nz, zx_music_loc_7851
zx_music_loc_787C:
zx_music_init_voice1:
    jr zx_music_init_voices
zx_music_loc_7882:
    ld (zx_music_loc_788C+1),a
    jr zx_music_loc_7851
zx_music_loc_7888:
    call zx_music_note_ratio
    ld d,a
zx_music_loc_788C:
    ld a, 0
    push hl
    push de
    call zx_music_vyber_obalky
    ld (zx_music_obalka_hlas_1+1),hl
    ex de,hl
    ld (zx_music_vystup_hlas_1+1),hl
    pop de
    pop hl
    ld a, 5
    ld (zx_music_loc_784E+1),hl
    ld hl, zx_music_var_7F8F
zx_music_loc_78A4:
    ld (zx_music_loc_7848+1),a
zx_music_loc_78A7:
    ; Dekodér druhého hlasu.
    ld a, 0
    sub (hl)
    jr nz, zx_music_loc_78FD
zx_music_loc_78AD:
    ld hl, 0
zx_music_loc_78B0:
    ld a, (hl)
    inc hl
    and a
    jp p, zx_music_loc_78E4
    inc a
    jr z, zx_music_loc_78C9
    inc a
    ld a, (hl)
    inc hl
    jr z, zx_music_loc_78DE
    ld (zx_music_var_7F8E),a
    ld (zx_music_loc_7A3D+1),a
    jr zx_music_loc_78B0
zx_music_loc_78C9:
    ld hl, 0
    push de
    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl
    ld (zx_music_loc_78C9+1),hl
    ld a, d
    or e
    ex de,hl
    pop de
    jr nz, zx_music_loc_78B0
zx_music_loc_78DB:
    jr zx_music_init_voice1
zx_music_loc_78DE:
    ld (zx_music_loc_78E8+1),a
    jr zx_music_loc_78B0
zx_music_loc_78E4:
    call zx_music_note_ratio
    ld e,a
zx_music_loc_78E8:
    ld a, 0
    push hl
    push de
    call zx_music_vyber_obalky
    ld (zx_music_obalka_hlas_2+1),hl
    ex de,hl
    ld (zx_music_vystup_hlas_2+1),hl
    pop de
    pop hl
    ld a, (hl)
    inc hl
    ld (zx_music_loc_78AD+1),hl
zx_music_loc_78FD:
    ld (zx_music_loc_78A7+1),a
    ld h,a
    ld a, (zx_music_loc_7848+1)
    cp h
    jr c, zx_music_loc_7909
    ld a, h
zx_music_loc_7909:
    ld (zx_music_var_7F8F),a
    ld (zx_music_var_7F8C),a
    call zx_music_loc_792A

; Bit 0 společně ze řádků kláves Enter a 0.
zx_music_key:
    ld a,$AF
    in a,($FE)
    rrca
    jp c,zx_music_main_loop
    ei
    ret
zx_music_note_ratio:
    ; Převod indexu noty na délku časovací smyčky.
    push hl
    ld h,zx_music_note_periods >> 8
    add a,zx_music_note_periods & $ff
    ld l,a
    jr nc,zx_music_notrat_skip
    inc h
zx_music_notrat_skip:
    ld a,(hl)
    sub $06
    pop hl
    ret
zx_music_vyber_obalky:
    add a,a
    ld l,a
    ld h,$00
    ld de,zx_music_envelope_table
    add hl,de
    ld e, (hl)
    inc hl
    ld d, (hl)
    dec hl
    ret
zx_music_loc_7924:
    ; Časování noty. Zdánlivě prázdné instrukce i dvojice EX (SP),HL
    ; jsou součástí prodlev přepočítaných z PMD na Spectrum; neodstraňovat.
    ld a,a
    ld a,a
    ld a,a
    ld a,a
    ex (sp),hl
    ex (sp),hl
zx_music_loc_792A:
    ld a, b
    cp c
    jr nc, zx_music_loc_799E
    ld a, b
    add a, 6
    ld l,a
    sub $0A
    push hl
    pop hl
    ex (sp),hl
    ex (sp),hl
zx_music_loc_793B:
    dec a
    ld a,a
    ld a,a
    ld a,a
    ex (sp),hl
    ex (sp),hl
    ex (sp),hl
    ex (sp),hl
    jr nz, zx_music_loc_793B
    ld a, l
    sub c
    jr nc, zx_music_loc_7985
    add a, 4
    jr nc, zx_music_loc_7974
    ld a, d
    add a, b
    sub c
    ld b,a
    ld a, c
    sub l
    ld h,a
    ld a, c
    add a, 6
    ld l,a
    ld c, e
    call zx_music_vystup_hlas_1
zx_music_loc_7961:
    dec h
    ld a,a
    ld a,a
    ld a,a
    ex (sp),hl
    ex (sp),hl
    ex (sp),hl
    ex (sp),hl
    jp nz, zx_music_loc_7961
    call zx_music_vystup_hlas_2
    jp zx_music_loc_7A07
zx_music_loc_7974:
    ex (sp),hl
    ex (sp),hl
    push hl
    pop hl
    ld a,a
    ld a,a
    ld a,a
    ld a, c
    sub l
    ld c,a
    ld b, d
    call zx_music_vystup_hlas_1
    jp zx_music_loc_7A07
zx_music_loc_7985:
    ld a, c
    add a, e
    sub l
    ld c,a
    ld a, d
    sub 6
    ld b,a
    ld a, l
    add a, 6
    ld l,a
    ld a,a
    nop
    ld a,a
    ld a,a
    call zx_music_vystup_hlas_1
    call zx_music_vystup_hlas_2
    jr zx_music_loc_7A07
zx_music_loc_799E:
    ld a, c
    add a, 6
    ld l,a
    sub $0A
zx_music_loc_79A4:
    dec a
    ld a,a
    ld a,a
    ld a,a
    ex (sp),hl
    ex (sp),hl
    ex (sp),hl
    ex (sp),hl
    jr nz, zx_music_loc_79A4
    ld a, l
    sub b
    jr nc, zx_music_loc_79EE
    add a, 4
    jr nc, zx_music_loc_79DD
    ld a, e
    add a, c
    sub b
    ld c,a
    ld a, b
    sub l
    ld h,a
    ld a, b
    add a, 6
    ld l,a
    ld b, d
    call zx_music_vystup_hlas_2
zx_music_loc_79CA:
    dec h
    ld a,a
    ld a,a
    ld a,a
    ex (sp),hl
    ex (sp),hl
    ex (sp),hl
    ex (sp),hl
    jr nz, zx_music_loc_79CA
    call zx_music_vystup_hlas_1
    jr zx_music_loc_7A07
zx_music_loc_79DD:
    ex (sp),hl
    ex (sp),hl
    push hl
    pop hl
    ld a,a
    ld a,a
    ld a,a
    ld a, b
    sub l
    ld b,a
    ld c, e
    call zx_music_vystup_hlas_2
    jr zx_music_loc_7A07
zx_music_loc_79EE:
    ld a, b
    add a, d
    sub l
    ld b,a
    ld a, e
    sub 6
    ld c,a
    ld a, l
    add a, 6
    ld l,a
    ld a,a
    nop
    ld a,a
    ld a,a
    call zx_music_vystup_hlas_2
    call zx_music_vystup_hlas_1
    jr zx_music_loc_7A07
zx_music_loc_7A07:
    ld a, 0
    add a, l
    ld (zx_music_loc_7A07+1),a
    jp nc, zx_music_loc_7924
    ld hl, zx_music_var_7F8B
    dec (hl)
    jp nz, zx_music_loc_792A
    ld (hl), 3
    push de
    ld hl, zx_music_var_7F8D
    dec (hl)
    jp nz, zx_music_loc_7A36
zx_music_loc_7A21:
    ld (hl), $32
zx_music_obalka_hlas_1:
    ld hl, zx_music_envelope_table
    dec hl
    ld d, (hl)
    dec hl
    ld e, (hl)
    ld a, d
    or e
    jr z, zx_music_loc_7A36
    ld (zx_music_obalka_hlas_1+1),hl
    ex de,hl
    ld (zx_music_vystup_hlas_1+1),hl
zx_music_loc_7A36:
    ld hl, zx_music_var_7F8E
    dec (hl)
    jr nz, zx_music_loc_7A52
zx_music_loc_7A3D:
    ld (hl), $32
zx_music_obalka_hlas_2:
    ld hl, zx_music_envelope_table
    dec hl
    ld d, (hl)
    dec hl
    ld e, (hl)
    ld a, d
    or e
    jr z, zx_music_loc_7A52
    ld (zx_music_obalka_hlas_2+1),hl
    ex de,hl
    ld (zx_music_vystup_hlas_2+1),hl
zx_music_loc_7A52:
    ld hl, zx_music_var_7F8C
    pop de
    dec (hl)
    jp nz, zx_music_loc_792A
    ret
zx_music_vystup_hlas_1:
    jp zx_music_no_pulz
zx_music_vystup_hlas_2:
    jp zx_music_no_pulz
zx_music_no_pulz:
    ld a,17
zx_music_wait_1:
zx_music_wait_2:
    push hl
    pop hl
    dec a
    jr nz, zx_music_wait_2
    ret
zx_music_pulz_14T:
    ld a, $0D
    call zx_music_wait_2
    ld a,a
    ld a, $10
    out ($fe),a
zx_music_pulz_off:
    xor a
    out ($fe),a
    ret
zx_music_pulz_26T:
    ld a, $0C
    call zx_music_wait_1
    push hl
    pop hl
    ld a, $10
    out ($fe),a
    jr zx_music_pulz_off
zx_music_pulz_50T:
    ld a, $0C
    call zx_music_wait_1
    ld a, $10
    out ($fe),a
    push hl
    pop hl
    jr zx_music_pulz_off
zx_music_pulz_10w1:
    ld a,1
    jr zx_music_pulz_set
zx_music_pulz_9w2:
    ld a,2
    jr zx_music_pulz_set
zx_music_pulz_8w3:
    ld a,3
    jr zx_music_pulz_set
zx_music_pulz_7w4:
    ld a,4
    jr zx_music_pulz_set
zx_music_pulz_6w5:
    ld a,5
    jr zx_music_pulz_set
zx_music_pulz_5w6:
    ld a,6
    jr zx_music_pulz_set
zx_music_pulz_4w7:
    ld a,7
    jr zx_music_pulz_set
zx_music_pulz_3w8:
    ld a,8
    jr zx_music_pulz_set
zx_music_pulz_2w9:
    ld a,9
    jr zx_music_pulz_set
zx_music_pulz_1w10:
    ld a,10
    jr zx_music_pulz_set
zx_music_pulz_set:
    ld ixl,a
    cpl
    add a,12
    call zx_music_wait_1
zx_music_pulz_long:
    ld a,$10
    out ($fe),a
    ld a,ixl
    call zx_music_wait_2
    jr zx_music_pulz_off
zx_music_pulz_s2w11:
    ex (sp),hl
    ex (sp),hl
    ex (sp),hl
    ex (sp),hl
    ld ixl,$0B
    jr zx_music_pulz_long
zx_music_pulz_s0w13:
    ld ixl,$0D
    jr zx_music_pulz_long
zx_music_code_end:
    ; Nulové zakončení obálek, tabulka pulzů, periody, pořadí a motivy hlasů.
    defw 0
zx_music_envelope_table:
    defw zx_music_no_pulz
    defw zx_music_pulz_14T
    defw zx_music_pulz_26T
    defw zx_music_pulz_50T
    defw zx_music_pulz_10w1
    defw zx_music_pulz_9w2
    defw zx_music_pulz_8w3
    defw zx_music_pulz_7w4
    defw zx_music_pulz_6w5
    defw zx_music_pulz_5w6
    defw zx_music_pulz_4w7
    defw zx_music_pulz_3w8
    defw zx_music_pulz_2w9
    defw zx_music_pulz_1w10
    defw zx_music_pulz_s2w11
    defw zx_music_pulz_s0w13
zx_music_note_periods:
    defb $FF
    defb $F0
    defb $E3
    defb $D7
    defb $CB
    defb $C0
    defb $B4
    defb $AB
    defb $A1
    defb $97
    defb $90
    defb $88
    defb $80
    defb $79
    defb $72
    defb $6C
    defb $66
    defb $60
    defb $5B
    defb $56
    defb $51
    defb $4C
    defb $48
    defb $44
    defb $40
    defb $3D
    defb $39
    defb $36
    defb $33
    defb $30
    defb $2D
    defb $2B
    defb $28
    defb $26
    defb $24
    defb $22
    defb $20
    defb $1E
    defb $1C
    defb $1B
    defb $19
    defb $18
    defb $17
    defb $15
    defb $14
    defb $13
    defb $12
    defb $11
    defb $10
    defb $0F
    defb $0E
    defb $0D
    defb $0C
zx_music_voice1_order:
    defw zx_music_byte_7D85
    defw zx_music_byte_7E01
    defw zx_music_byte_7D5D
    defw zx_music_byte_7E01
    defw zx_music_byte_7D62
    defw zx_music_byte_7E0A
    defw zx_music_byte_7D67
    defw zx_music_byte_7E0A
    defw zx_music_byte_7D6C
    defw zx_music_byte_7DED
    defw zx_music_byte_7D71
    defw zx_music_byte_7DED
    defw zx_music_byte_7D76
    defw zx_music_byte_7E13
    defw zx_music_byte_7D7B
    defw zx_music_byte_7E0A
    defw zx_music_byte_7D80
    defw zx_music_byte_7E01
    defw zx_music_byte_7E01
    defw zx_music_byte_7E0A
    defw zx_music_byte_7E0A
    defw zx_music_byte_7DED
    defw zx_music_byte_7DED
    defw zx_music_byte_7E13
    defw zx_music_byte_7E0A
    defw zx_music_byte_7E01
    defw zx_music_byte_7E01
    defw zx_music_byte_7E0A
    defw zx_music_byte_7E0A
    defw zx_music_byte_7DED
    defw zx_music_byte_7DED
    defw zx_music_byte_7E13
    defw zx_music_byte_7E0A
    defw zx_music_byte_7E01
    defw zx_music_byte_7E01
    defw zx_music_byte_7E0A
    defw zx_music_byte_7E0A
    defw zx_music_byte_7DED
    defw zx_music_byte_7DED
    defw zx_music_byte_7E13
    defw zx_music_byte_7E0A
    defw zx_music_byte_7DDB
    defw zx_music_byte_7DDB
    defw zx_music_byte_7DDB
    defw zx_music_byte_7DDB
    defw zx_music_byte_7DC9
    defw zx_music_byte_7DC9
    defw zx_music_byte_7DAE
    defw zx_music_byte_7DAE
    defw zx_music_byte_7DDB
    defw zx_music_byte_7DDB
    defw zx_music_byte_7DDB
    defw zx_music_byte_7DDB
    defw zx_music_byte_7DC9
    defw zx_music_byte_7DC9
    defw zx_music_byte_7DAE
    defw zx_music_byte_7DAE
    defw zx_music_byte_7E01
    defw zx_music_byte_7E01
    defw zx_music_byte_7E0A
    defw zx_music_byte_7E0A
    defw zx_music_byte_7DED
    defw zx_music_byte_7DED
    defw zx_music_byte_7E13
    defw zx_music_byte_7E0A
    defw zx_music_byte_7E01
    defw zx_music_byte_7E01
    defw zx_music_byte_7E0A
    defw zx_music_byte_7E0A
    defw zx_music_byte_7DED
    defw zx_music_byte_7DED
    defw zx_music_byte_7E13
    defw zx_music_byte_7E0A
    defw zx_music_byte_7E01
    defw zx_music_byte_7E01
    defw zx_music_byte_7E0A
    defw zx_music_byte_7E0A
    defw zx_music_byte_7DED
    defw zx_music_byte_7DED
    defw zx_music_byte_7E13
    defw zx_music_byte_7E0A
    defw zx_music_byte_7E01
    defw zx_music_byte_7E01
    defw zx_music_byte_7E0A
    defw zx_music_byte_7E0A
    defw zx_music_byte_7DED
    defw zx_music_byte_7DED
    defw zx_music_byte_7E13
    defw zx_music_byte_7E0A
    defw zx_music_byte_7DDB
    defw zx_music_byte_7DDB
    defw zx_music_byte_7DDB
    defw zx_music_byte_7DDB
    defw zx_music_byte_7DC9
    defw zx_music_byte_7DC9
    defw zx_music_byte_7DAE
    defw zx_music_byte_7DAE
    defw zx_music_byte_7DDB
    defw zx_music_byte_7DDB
    defw zx_music_byte_7DDB
    defw zx_music_byte_7DDB
    defw zx_music_byte_7DC9
    defw zx_music_byte_7DC9
    defw zx_music_byte_7DAE
    defw zx_music_byte_7DAE
    defw zx_music_byte_7E01
    defw zx_music_byte_7E01
    defw zx_music_byte_7E0A
    defw zx_music_byte_7E0A
    defw zx_music_byte_7DED
    defw zx_music_byte_7DED
    defw zx_music_byte_7E13
    defw zx_music_byte_7E0A
    defw zx_music_byte_7DDB
    defw zx_music_byte_7DDB
    defw zx_music_byte_7DAE
    defw zx_music_byte_7DAE
    defw zx_music_byte_7DC9
    defw zx_music_byte_7DC9
    defw zx_music_byte_7D8A
    defw zx_music_byte_7DAE
    defw zx_music_byte_7DF6
    defw zx_music_byte_7DF6
    defw zx_music_byte_7DF6
    defw zx_music_byte_7DF6
    defw zx_music_byte_7D9C
    defw zx_music_byte_7D9C
    defw zx_music_byte_7D9C
    defw zx_music_byte_7D9C
    defw zx_music_byte_7DB7
    defw zx_music_byte_7DB7
    defw zx_music_byte_7DC0
    defw zx_music_byte_7DC0
    defw zx_music_byte_7DF6
    defw zx_music_byte_7DF6
    defw zx_music_byte_7DF6
    defw zx_music_byte_7DF6
    defw zx_music_byte_7DA5
    defw zx_music_byte_7DA5
    defw zx_music_byte_7DA5
    defw zx_music_byte_7DA5
    defw zx_music_byte_7D93
    defw zx_music_byte_7D93
    defw zx_music_byte_7D93
    defw zx_music_byte_7D93
    defw zx_music_byte_7DD2
    defw zx_music_byte_7DD2
    defw zx_music_byte_7DE4
    defw zx_music_byte_7DE4
    defw zx_music_byte_7DA5
    defw zx_music_byte_7DA5
    defw zx_music_byte_7DA5
    defw zx_music_byte_7DA5
    defw zx_music_byte_7E13
    defw zx_music_byte_7E13
    defw zx_music_byte_7E0A
    defw zx_music_byte_7E0A
    defw zx_music_byte_7E01
    defw zx_music_byte_7E01
    defw zx_music_byte_7E0A
    defw zx_music_byte_7E0A
    defw zx_music_byte_7DED
    defw zx_music_byte_7DED
    defw zx_music_byte_7E13
    defw zx_music_byte_7E0A
    defw zx_music_byte_7D80
    defw zx_music_byte_7E01
    defw zx_music_byte_7D7B
    defw zx_music_byte_7E01
    defw zx_music_byte_7D76
    defw zx_music_byte_7E0A
    defw zx_music_byte_7D71
    defw zx_music_byte_7E0A
    defw zx_music_byte_7D6C
    defw zx_music_byte_7DED
    defw zx_music_byte_7D67
    defw zx_music_byte_7DED
    defw zx_music_byte_7D62
    defw zx_music_byte_7E13
    defw zx_music_byte_7D5D
    defw zx_music_byte_7E0A
    defw zx_music_byte_7D85
    defw zx_music_byte_7E01
    defw zx_music_byte_7DFF
    defw zx_music_byte_7E0A
    defw zx_music_byte_7E0A
    defw zx_music_byte_7DED
    defw zx_music_byte_7DED
    defw zx_music_byte_7E13
    defw zx_music_byte_7E0A
    defw 0
zx_music_byte_7D5D:
    defb $0FE
    defb 2
    defb $0FD
    defb 5
    defb $0FF
zx_music_byte_7D62:
    defb $0FE
    defb 3
    defb $0FD
    defb 4
    defb $0FF
zx_music_byte_7D67:
    defb $0FE
    defb 4
    defb $0FD
    defb 3
    defb $0FF
zx_music_byte_7D6C:
    defb $0FE
    defb 5
    defb $0FD
    defb 2
    defb $0FF
zx_music_byte_7D71:
    defb $0FE
    defb 7
    defb $0FD
    defb 2
    defb $0FF
zx_music_byte_7D76:
    defb $0FE
    defb 9
    defb $0FD
    defb 1
    defb $0FF
zx_music_byte_7D7B:
    defb $0FE
    defb $0B
    defb $0FD
    defb 1
    defb $0FF
zx_music_byte_7D80:
    defb $0FE
    defb $0D
    defb $0FD
    defb 1
    defb $0FF
zx_music_byte_7D85:
    defb $0FD
    defb $0C8
    defb $0FE
    defb 1
    defb $0FF
zx_music_byte_7D8A:
    defb $0E
    defb $12
    defb $17
    defb $0E
    defb $17
    defb $12
    defb $0E
    defb $17
    defb $0FF
zx_music_byte_7D93:
    defb $0F
    defb $13
    defb $18
    defb $0F
    defb $18
    defb $13
    defb $0F
    defb $18
    defb $0FF
zx_music_byte_7D9C:
    defb $0C
    defb $10
    defb $15
    defb $0C
    defb $15
    defb $10
    defb $0C
    defb $15
    defb $0FF
zx_music_byte_7DA5:
    defb 8
    defb $0F
    defb $14
    defb $0C
    defb $14
    defb $0F
    defb $0C
    defb $0F
    defb $0FF
zx_music_byte_7DAE:
    defb 9
    defb $10
    defb $15
    defb $0D
    defb $15
    defb $10
    defb $0D
    defb $10
    defb $0FF
zx_music_byte_7DB7:
    defb $0A
    defb $11
    defb $16
    defb $0E
    defb $16
    defb $11
    defb $0E
    defb $11
    defb $0FF
zx_music_byte_7DC0:
    defb $0C
    defb $13
    defb $18
    defb $10
    defb $18
    defb $13
    defb $10
    defb $13
    defb $0FF
zx_music_byte_7DC9:
    defb $0E
    defb $13
    defb $17
    defb 7
    defb $17
    defb $13
    defb $0E
    defb $17
    defb $0FF
zx_music_byte_7DD2:
    defb $0D
    defb $11
    defb $14
    defb 8
    defb $14
    defb $11
    defb $0D
    defb $11
    defb $0FF
zx_music_byte_7DDB:
    defb $0E
    defb $12
    defb $15
    defb $0E
    defb 9
    defb $12
    defb $0E
    defb $12
    defb $0FF
zx_music_byte_7DE4:
    defb 3
    defb $0A
    defb $13
    defb $0F
    defb $0A
    defb $13
    defb $0F
    defb $0A
    defb $0FF
zx_music_byte_7DED:
    defb 4
    defb $0B
    defb $14
    defb $0B
    defb 4
    defb $14
    defb $10
    defb $0B
    defb $0FF
zx_music_byte_7DF6:
    defb 5
    defb $0C
    defb $15
    defb $0C
    defb 5
    defb $15
    defb $11
    defb $0C
    defb $0FF
zx_music_byte_7DFF:
    defb $0FE
    defb 0
zx_music_byte_7E01:
    defb $0B
    defb $12
    defb $17
    defb $12
    defb $0B
    defb $0F
    defb $12
    defb $0F
    defb $0FF
zx_music_byte_7E0A:
    defb 6
    defb $12
    defb $16
    defb $0D
    defb $16
    defb $12
    defb $0D
    defb $12
    defb $0FF
zx_music_byte_7E13:
    defb $0F
    defb $14
    defb $17
    defb $14
    defb 8
    defb $14
    defb $0F
    defb $0B
    defb $0FF
zx_music_voice2_order:
    defw zx_music_voice2_patt
    defw zx_music_byte_7F84
    defw zx_music_byte_7F84
    defw zx_music_byte_7F84
    defw zx_music_byte_7F84
    defw zx_music_byte_7E51
    defw zx_music_byte_7E51
    defw zx_music_byte_7EB9
    defw zx_music_byte_7ECA
    defw zx_music_byte_7EB9
    defw zx_music_byte_7ED5
    defw zx_music_byte_7F84
    defw zx_music_byte_7F84
    defw zx_music_byte_7E51
    defw zx_music_byte_7E51
    defw zx_music_byte_7EB9
    defw zx_music_byte_7ECA
    defw zx_music_byte_7EB9
    defw zx_music_byte_7ED5
    defw zx_music_byte_7EFC
    defw zx_music_byte_7E51
    defw zx_music_byte_7E78
    defw zx_music_byte_7F84
    defw 0
zx_music_voice2_patt:
    defb $0FD
    defb 9
    defb $0FE
    defb $0F
    defb $0FF
zx_music_byte_7E51:
    defb $0F
    defb $1E
    defb $0FD
    defb 3
    defb 6
    defb $0A
    defb $0FD
    defb 9
    defb 6
    defb $46
    defb 6
    defb $0A
    defb $0B
    defb $0A
    defb $0D
    defb $0A
    defb $0F
    defb $0A
    defb $10
    defb $0A
    defb $12
    defb $3C
    defb $10
    defb $0A
    defb $0F
    defb $0A
    defb $10
    defb $0A
    defb $0F
    defb $0A
    defb $0D
    defb $0A
    defb $0F
    defb $14
    defb $0D
    defb $0A
    defb $0B
    defb $14
    defb $0FF
zx_music_byte_7E78:
    defb $0FE
    defb $0E
    defb $0F
    defb $1E
    defb $0FD
    defb 3
    defb 6
    defb $0A
    defb $0FE
    defb $0D
    defb $0FD
    defb 9
    defb 6
    defb $46
    defb $0FE
    defb $0C
    defb 6
    defb $0A
    defb $0FE
    defb $0B
    defb $0B
    defb $0A
    defb $0D
    defb $0A
    defb $0FE
    defb $0A
    defb $0F
    defb $0A
    defb $0FE
    defb 9
    defb $10
    defb $0A
    defb $12
    defb $3C
    defb $0FE
    defb 8
    defb $10
    defb $0A
    defb $0F
    defb $0A
    defb $0FE
    defb 7
    defb $10
    defb $0A
    defb $0FE
    defb 6
    defb $0F
    defb $0A
    defb $0FE
    defb 5
    defb $0D
    defb $0A
    defb $0FE
    defb 4
    defb $0F
    defb $14
    defb $0FE
    defb 3
    defb $0D
    defb $0A
    defb $0FE
    defb 2
    defb $0B
    defb $14
    defb $0FF
zx_music_byte_7EB9:
    defb $0FD
    defb 7
    defb $12
    defb $1E
    defb $0FD
    defb 9
    defb $12
    defb $28
    defb $15
    defb $0A
    defb $13
    defb $14
    defb 9
    defb $14
    defb $0E
    defb $14
    defb $0FF
zx_music_byte_7ECA:
    defb $17
    defb $14
    defb $15
    defb $1E
    defb $12
    defb $1E
    defb $13
    defb $14
    defb $10
    defb $50
    defb $0FF
zx_music_byte_7ED5:
    defb $13
    defb $14
    defb $12
    defb $1E
    defb $12
    defb $1E
    defb $13
    defb $14
    defb $10
    defb $14
    defb $10
    defb $14
    defb $0E
    defb $14
    defb $0D
    defb $14
    defb $0B
    defb $1E
    defb $12
    defb $6E
    defb $10
    defb $0A
    defb $0F
    defb $0A
    defb $10
    defb $0A
    defb $0F
    defb $0A
    defb $0D
    defb $0A
    defb $0F
    defb $14
    defb $0D
    defb $0A
    defb $0B
    defb $0A
    defb $0D
    defb $5A
    defb $0FF
zx_music_byte_7EFC:
    defb $0E
    defb $1E
    defb $15
    defb $6E
    defb $13
    defb $0A
    defb $12
    defb $0A
    defb $13
    defb $0A
    defb $12
    defb $0A
    defb $10
    defb $0A
    defb $12
    defb $14
    defb $10
    defb $0A
    defb $0E
    defb $0A
    defb $10
    defb $5A
    defb $11
    defb $1E
    defb $18
    defb $50
    defb $0FD
    defb 3
    defb $18
    defb $0A
    defb $0FD
    defb 5
    defb $18
    defb $0F
    defb $16
    defb $0F
    defb $15
    defb $0A
    defb $0FD
    defb 9
    defb $10
    defb $1E
    defb $0C
    defb $50
    defb $0FD
    defb 3
    defb $0C
    defb $0A
    defb $0FD
    defb 5
    defb $0C
    defb $0F
    defb $0E
    defb $0F
    defb $10
    defb $0A
    defb $0FD
    defb 9
    defb $0E
    defb $46
    defb $13
    defb 5
    defb $11
    defb 5
    defb $10
    defb $14
    defb $10
    defb $14
    defb $11
    defb $14
    defb $13
    defb $14
    defb $15
    defb $46
    defb $15
    defb 5
    defb $16
    defb 5
    defb $18
    defb $0A
    defb $16
    defb $0A
    defb $15
    defb $0A
    defb $11
    defb $14
    defb $0E
    defb $0A
    defb $0C
    defb $14
    defb $14
    defb $46
    defb $14
    defb 5
    defb $16
    defb 5
    defb $0FD
    defb 5
    defb $18
    defb $14
    defb $18
    defb $14
    defb $16
    defb $14
    defb $14
    defb $14
    defb $0FD
    defb 9
    defb $18
    defb $1E
    defb $13
    defb $82
    defb $11
    defb $46
    defb $1D
    defb $0A
    defb $1B
    defb $14
    defb $16
    defb $14
    defb $18
    defb $14
    defb $0FD
    defb 5
    defb $19
    defb $14
    defb $0FD
    defb 9
    defb $19
    defb $1E
    defb $18
    defb 5
    defb $16
    defb 5
    defb $18
    defb $78
zx_music_byte_7F84:
    defb $0FE
    defb 0
    defb 0
    defb $0A0
    defb $0FE
    defb $0F
    defb $0FF
zx_music_data_end:
    ; Pět pracovních bajtů za původním koncem souboru COD.
zx_music_var_7F8B:
    defb 0
zx_music_var_7F8C:
    defb 0
zx_music_var_7F8D:
    defb 0
zx_music_var_7F8E:
    defb 0
zx_music_var_7F8F:
    defb 0
zx_music_end:
