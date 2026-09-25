; Nativní vrstva ZX Spectrum 48K. Krátké úseky se zásobníkem v grafických
; datech běží s DI; ostatní kód používá 50Hz přerušení IM2.
zx_boot:
    di
    ld sp,$fff0
    ld hl,$5b00
    ld de,$5b01
    ld bc,255
    ld (hl),0
    ldir
    ld hl,zx_irq_template
    ld de,zx_irq
    ld bc,zx_irq_template_end-zx_irq_template
    ldir
    ; TAP obsahuje jen statický kód a data. Pracovní fronty a IM2 vzniknou
    ; až po načtení; zbytek pracovního obrazu maže běžný start hry.
    ld hl,$c59d
    ld de,$c59e
    ld bc,$262
    ld (hl),0
    ldir
    ld hl,$fe00
    ld de,$fe01
    ld bc,256
    ld (hl),$5b
    ldir
    ld a,$fe
    ld i,a
    im 2
    xor a
    out ($fe),a
zx_restart:
    di
    ld sp,$fff0
    xor a
    ld (zx_game_active),a
    ld (zx_position_valid),a
    ld hl,$e000
    ld de,$e001
    ld bc,$13ff
    ld (hl),a
    ldir
    ld hl,$0d0e
    ld ($f1f8),hl
    ld hl,$1234
    ld ($f03a),hl
    ld hl,pmd_654d
    push hl
    jp pmd_58a4
zx_ret:
    ret
zx_irq_template:
    push af
    ld a,(zx_frames)
    inc a
    ld (zx_frames),a
    pop af
    ei
    reti
zx_irq_template_end:
zx_clear_buffer:
    ld hl,$c800
    ld de,$c801
    ld bc,$17ff
    ld (hl),0
    ldir
    ret
zx_mask_sp:
    di
    ld a,(hl)
    inc hl
    ld h,(hl)
    ld l,a
    jp pmd_4bfb
zx_sprite_sp:
    di
    ld sp,hl
    jp m,pmd_4d20
    jp pmd_4c70
zx_tile_sp:
    di
    ld sp,hl
    ld hl,($f1bb)
    jp (hl)
zx_restore_sp:
    ld sp,hl
    ei
    ret
zx_player_init:
    ld hl,pmd_5623
    ld ($f1fa),hl
    ret
zx_macro:
    push bc
    ld bc,$6000
    add hl,bc
    pop bc
    jp pmd_5764
zx_player_dispatch:
    ld de,pmd_64ab
    ld a,($f138)
    jp pmd_4e1a
zx_wait_frame:
    ei
    halt
    ret
zx_tick:
    push af
    push bc
    push de
    push hl
    ld a,(zx_frames)
    ld b,a
    ld a,(zx_deadline)
    sub b
    jr z,zx_tick_done
    cp 4
    jr nc,zx_tick_done
    call zx_wait_frame
    jr zx_tick+4
zx_tick_done:
    ld a,(zx_frames)
    add a,3
    ld (zx_deadline),a
    ld hl,(zx_step_count)
    inc hl
    ld (zx_step_count),hl
    call zx_move_sound
    ld a,($f17d)
    and $3f
    cp $3f
    jp z,zx_win
    ld a,$f7
    in a,($fe)
    bit 0,a
    jp z,zx_restart
    pop hl
    pop de
    pop bc
    pop af
    ei
    ret
; Tón až po dokončení kroku: PMD mění XYZ v různých fázích podle směru.
; Srovnávání každé mezifáze vytvářelo při zatočení dvě pípnutí těsně za sebou.
; Během pádu je ticho, dopad má jeden tón. První tick jen uloží polohu.
; Registry chrání volající zx_tick.
zx_move_sound:
    ld a,(zx_last_motion_state)
    ld b,a
    ld a,($f138)
    ld (zx_last_motion_state),a
    ld d,a
    ld hl,zx_position_valid
    ld a,(hl)
    ld (hl),1
    or a
    jp z,zx_capture_position
    ld a,d
    cp $3e
    ret z
    ld a,b
    cp $3e
    jr nz,zx_move_finished
    ld a,d
    cp $3f
    jr z,zx_move_landed
    cp $46
    jr z,zx_move_landed
zx_move_finished:
    ld a,d
    cp 1
    ret nz
    call zx_capture_position
    ld a,c
    or a
    ret z
    jr zx_move_beep
zx_move_landed:
    call zx_capture_position
    jr zx_move_beep
zx_capture_position:
    ld hl,$f135
    ld de,zx_last_position
    ld b,3
    ld c,0
zx_compare_position:
    ld a,(de)
    cp (hl)
    jr z,zx_same_coordinate
    inc c
zx_same_coordinate:
    ld a,(hl)
    ld (de),a
    inc hl
    inc de
    djnz zx_compare_position
    ld a,($f1f0)
    ld hl,zx_last_room
    cp (hl)
    ld (hl),a
    jr z,zx_same_room
    inc c
zx_same_room:
    ret
zx_move_beep:
    ; Původní krátký efekt smrti: 12 přepnutí beeperu, černý okraj.
    xor a
    ld c,12
zx_move_tone:
    xor 16
    out ($fe),a
    ld b,32
zx_move_tone_delay:
    djnz zx_move_tone_delay
    dec c
    jr nz,zx_move_tone
    xor a
    out ($fe),a
    ret
; Bity logiky: 0 vpravo dolů, 1 vlevo nahoru,
; 2 vpravo nahoru, 3 vlevo dolů. Směry kláves a páčky:
; Q/7/nahoru vlevo nahoru, A/6/dolů vpravo dolů,
; O/5/vlevo vlevo dolů, P/8/vpravo vpravo nahoru.
zx_input:
    ld b,0
    ld a,$fb
    in a,($fe)
    bit 0,a
    jr nz,zx_no_q
    set 1,b
zx_no_q:
    ld a,$fd
    in a,($fe)
    bit 0,a
    jr nz,zx_no_a
    set 0,b
zx_no_a:
    ld a,$df
    in a,($fe)
    bit 1,a
    jr nz,zx_no_o
    set 3,b
zx_no_o:
    bit 0,a
    jr nz,zx_no_p
    set 2,b
zx_no_p:
    ld a,$ef
    in a,($fe)
    bit 3,a
    jr nz,zx_no_7
    set 1,b
zx_no_7:
    bit 4,a
    jr nz,zx_no_6
    set 0,b
zx_no_6:
    bit 2,a
    jr nz,zx_no_8
    set 2,b
zx_no_8:
    ld a,$f7
    in a,($fe)
    bit 4,a
    jr nz,zx_no_5
    set 3,b
zx_no_5:
    ; Nepřipojený port může vracet floating bus. Čte se jen po volbě J.
    ld a,(zx_kempston)
    or a
    jr z,zx_keys_ready
    in a,($1f)
    ld c,a
    and $e0
    jr nz,zx_keys_ready
    bit 0,c
    jr z,zx_joy_left
    set 2,b
zx_joy_left:
    bit 1,c
    jr z,zx_joy_down
    set 3,b
zx_joy_down:
    bit 2,c
    jr z,zx_joy_up
    set 0,b
zx_joy_up:
    bit 3,c
    jr z,zx_keys_ready
    set 1,b
zx_keys_ready:
    ld a,b
    ld ($f238),a
    jp pmd_566d
; Převod 4 PMD bajtů (LSB vlevo, 6 bodů) na 3 ZX bajty.
; Zobrazení je 192 x 192, uprostřed obrazovky, bez ztráty pixelů.
zx_full_present:
    push af
    push bc
    push de
    push hl
    ; Původní náhodné odkrývání obrazu posunulo RNG přesně 1024krát.
    ; f(x)=73*x-1, f^1024(x)=$a001*x+$8c00 (mod 65536).
    ld hl,($f03a)
    ld a,l
    rrca
    rrca
    rrca
    and $e0
    ld b,a
    add a,a
    add a,a
    add a,b
    add a,$8c
    add a,h
    ld h,a
    ld ($f03a),hl
    ld hl,$c600
    ld ($f1b8),hl
    xor a
    ld ($f1ba),a
    ; Okraj nové místnosti je výchozí poloha, nikoli další krok pro beeper.
    ; První tick uloží souřadnice i stav pádu; další krok či dopad už zazní.
    ld (zx_position_valid),a
    ld a,1
    ld (zx_game_active),a
    ld ix,$c800
    ld de,$4004
    ld b,192
zx_row:
    push bc
    push de
    ld b,8
    call zx_convert_groups
    pop de
    inc d
    ld a,d
    and 7
    jr nz,zx_next_row
    ld a,e
    add a,32
    ld e,a
    jr c,zx_next_row
    ld a,d
    sub 8
    ld d,a
zx_next_row:
    pop bc
    djnz zx_row
    call zx_crowns
    pop hl
    pop de
    pop bc
    pop af
    ret
zx_convert_groups:
zx_group:
    ld h,$60
    ld l,(ix+0)
    ld a,(hl)
    add a,a
    add a,a
    ld c,a
    ld l,(ix+1)
    ld a,(hl)
    rrca
    rrca
    rrca
    rrca
    and 3
    or c
    ld (de),a
    inc de
    ld a,(hl)
    rlca
    rlca
    rlca
    rlca
    and $f0
    ld c,a
    ld l,(ix+2)
    ld a,(hl)
    rrca
    rrca
    and 15
    or c
    ld (de),a
    inc de
    ld a,(hl)
    rrca
    rrca
    and $c0
    ld c,a
    ld l,(ix+3)
    ld a,(hl)
    or c
    ld (de),a
    inc de
    inc ix
    inc ix
    inc ix
    inc ix
    djnz zx_group
    ret
; Původní seznam změněných obdélníků: 4 šestipixelové bajty na řádek.
; Přenáší se nejvýše dvě sousední skupiny po 24 bodech, ne celá obrazovka.
zx_present:
    push af
    push bc
    push de
    push hl
zx_rect_list:
    ld hl,$f1ba
    ld a,(hl)
    or a
    jr z,zx_rect_done
    dec (hl)
    call pmd_5731
    call pmd_5731
    call pmd_573a
    ld b,a
    ld de,32
    add hl,de
    ld a,l
    and 3
    ld c,1
    jr z,zx_rect_row
    inc c
zx_rect_row:
    push bc
    push hl
    ld a,h
    sub $c8
    and $18
    or $40
    ld d,a
    ld a,l
    rlca
    rlca
    rlca
    and 7
    or d
    ld d,a
    ld a,h
    sub $c8
    and 7
    rrca
    rrca
    rrca
    ld e,a
    ld a,c
    ld (zx_group_count),a
    ld a,l
    and $1c
    rrca
    rrca
    ld c,a
    add a,a
    add a,c
    add a,4
    or e
    ld e,a
    ld a,l
    and $fc
    ld l,a
    push hl
    pop ix
    ld a,(zx_group_count)
    ld b,a
    call zx_convert_groups
    pop hl
    ld de,32
    add hl,de
    pop bc
    djnz zx_rect_row
    jr zx_rect_list
zx_rect_done:
    ; Původní fronta po sběru přenáší i staré oblasti ukazatelů.
    ; Nové korunky musí vzniknout až po ní, jinak smaže část paprsků.
    ld a,($f17d)
    ld hl,zx_last_crowns
    cp (hl)
    call nz,zx_crowns
    pop hl
    pop de
    pop bc
    pop af
    ret
zx_group_count: defb 0
; Ukazatele v rozích celého rastru 256 x 192. Používají původní PMD kresbu.
; Do herního bufferu se nekreslí, takže uvolněná místa zůstanou čistá.
zx_crowns:
    push af
    push bc
    push de
    push hl
    push ix
    ld hl,zx_crown_positions
    ld a,($f17d)
    ld (zx_last_crowns),a
    ld c,a
    ld b,6
zx_crown:
    ld e,(hl)
    inc hl
    ld d,(hl)
    inc hl
    push hl
    push bc
    ld ix,$a437
    ld b,27
zx_crown_row:
    push bc
    push de
    ld b,1
    call zx_convert_groups
    pop de
    pop bc
    bit 0,c
    jr nz,zx_crown_next_row
    ; Nesebraná korunka: pouze vnitřních 12 x 13 bodů, bez paprsků.
    ld h,d
    ld l,e
    ld a,b
    sub 8
    cp 13
    jr nc,zx_crown_blank_row
    ld a,(hl)
    and 3
    ld (hl),a
    inc hl
    inc hl
    ld a,(hl)
    and $c0
    ld (hl),a
    jr zx_crown_next_row
zx_crown_blank_row:
    xor a
    ld (hl),a
    inc hl
    ld (hl),a
    inc hl
    ld (hl),a
zx_crown_next_row:
    inc d
    ld a,d
    and 7
    jr nz,zx_crown_row_ready
    ld a,e
    add a,32
    ld e,a
    jr c,zx_crown_row_ready
    ld a,d
    sub 8
    ld d,a
zx_crown_row_ready:
    djnz zx_crown_row
    pop bc
    pop hl
    rrc c
    djnz zx_crown
    pop ix
    pop hl
    pop de
    pop bc
    pop af
    ret
zx_crown_positions:
    ; Pořadí bitů PMD: levá dolní vnitřní/vnější, pravá dolní vnitřní/vnější,
    ; levá horní, pravá horní. Souřadnice označují i okolní paprsky.
    defw $5583,$5160 ; x=24, y=165 / x=0, y=153
    defw $559a,$517d ; x=208, y=165 / x=232, y=153
    defw $4000,$401d ; x=0/232, y=0
zx_cls:
    ld hl,$4000
    ld de,$4001
    ld bc,$17ff
    ld (hl),0
    ldir
    ld hl,$5800
    ld de,$5801
    ld bc,$02ff
    ld (hl),7
    ldir
zx_home:
    xor a
    ld (zx_text_margin),a
    ld hl,0
    ld (zx_cursor),hl
    ret
zx_clear_text:
    jp zx_cls
; Vlastní tisk: všech 96 znaků z font_cz.bin, ikonky menu mají vlastní bitmapy.
zx_print:
    push af
    ld a,(zx_cursor)
    ld (zx_text_margin),a
    ld a,1
    ld (zx_plain),a
    pop af
zx_print_loop:
    ld a,(hl)
    inc hl
    or a
    jr z,zx_print_end
    call zx_text
    jr zx_print_loop
zx_print_end:
    ld (zx_plain),a
    ret
zx_plain: defb 0
zx_text_margin: defb 0
zx_text:
    push af
    push bc
    push de
    push hl
    cp 13
    jr z,zx_newline
    cp 12
    jr z,zx_text_home
    cp 28
    jr z,zx_text_cls
    cp 32
    jr c,zx_text_exit
    ld c,a
    ld a,(zx_plain)
    or a
    ld a,c
    jr nz,zx_ascii
    cp 48
    jr c,zx_spaces
    cp 96
    jr c,zx_ascii
    and 31
    add a,64
zx_ascii:
    cp $80
    jr c,zx_font_character
    cp ZX_MENU_GLYPHS_END
    jr nc,zx_text_exit
    sub ZX_PLOXON_TL
    ld de,zx_menu_icons
    jr zx_font_glyph
zx_font_character:
    ld de,zx_font-32*8
zx_font_glyph:
    ld l,a
    ld h,0
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,de
    ex de,hl
    ld hl,(zx_cursor)
    ld a,h
    cp 24
    jr nc,zx_text_exit
    and 7
    rrca
    rrca
    rrca
    or l
    ld c,a
    ld a,h
    and 24
    or $40
    ld h,a
    ld l,c
    ld b,8
zx_glyph:
    ld a,(de)
    inc de
    ld (hl),a
    inc h
    djnz zx_glyph
    ld hl,(zx_cursor)
    inc l
    ld a,l
    cp 32
    jr c,zx_cursor_store
zx_newline:
    ld hl,(zx_cursor)
    inc h
    ld a,(zx_text_margin)
    ld l,a
zx_cursor_store:
    ld (zx_cursor),hl
zx_text_exit:
    pop hl
    pop de
    pop bc
    pop af
    ret
zx_spaces:
    sub 31
    ld hl,(zx_cursor)
    add a,l
    ld l,a
    cp 32
    jr c,zx_cursor_store
    sub 32
    ld l,a
    inc h
    jr zx_cursor_store
zx_text_home:
    call zx_home
    jr zx_text_exit
zx_text_cls:
    call zx_cls
    jr zx_text_exit
zx_menu:
    call zx_cls
    ld hl,$0105
    ld (zx_cursor),hl
    ld hl,zx_title
    call zx_print
    ld hl,$0501
    ld (zx_cursor),hl
    ld hl,zx_help
    call zx_print
zx_menu_joystick:
    ld hl,$1501
    ld (zx_cursor),hl
    ld hl,zx_joy_label
    call zx_print
    ld hl,zx_joy_off
    ld a,(zx_kempston)
    or a
    jr z,zx_menu_joy_text
    ld hl,zx_joy_on
zx_menu_joy_text:
    call zx_print
zx_menu_wait:
    call zx_wait_frame
    ld a,$bf
    in a,($fe)
    bit 3,a
    jr nz,zx_menu_start_key
    ld a,(zx_kempston)
    xor 1
    ld (zx_kempston),a
    call zx_release
    jr zx_menu_joystick
zx_menu_start_key:
    call zx_menu_key
    jr nz,zx_menu_wait
    call zx_cls
    ld a,(zx_frames)
    ld ($f03a),a
    ld a,4
    ld (zx_deadline),a
    ei
    ret
zx_menu_key:
    ld a,$ef
    in a,($fe)
    and 1
    ret z
    ld a,$bf
    in a,($fe)
    and 1
    ret
zx_any_key:
    xor a
    in a,($fe)
    cpl
    and 31
    ret
zx_death:
    jp zx_game_over
zx_game_over_tick:
    ; Stav PMD $50 už nemá sprite: animace skončila. Původní čítač $F1F5
    ; přidával dalších 31 herních kroků s pohybujícím se Falmonem.
zx_game_over:
    xor a
    ld (zx_game_active),a
    ; Dokreslit poslední snímek smrtelné animace ještě před výkřikem.
    call zx_present
    call zx_death_sound
    call zx_cls
    call zx_results
    call zx_release
    jr zx_end_wait
; Krátký výkřik: rychlý náběh do výšky, chvění a pokles tónu.
; Volá se jednou při prohře, ještě nad posledním obrazem hry.
zx_death_sound:
    ld hl,zx_scream_periods
    ld d,0
zx_scream_next:
    ld a,(hl)
    inc hl
    or a
    jr z,zx_scream_end
    ld e,a
    ld c,24
zx_scream_pulse:
    ld a,d
    xor 16
    ld d,a
    out ($fe),a
    ld b,e
zx_scream_delay:
    djnz zx_scream_delay
    dec c
    jr nz,zx_scream_pulse
    jr zx_scream_next
zx_scream_end:
    xor a
    out ($fe),a
    ret
zx_scream_periods:
    defb 55,46,40,34,30,33,28,34,30,39,34,46
    defb 40,54,48,65,57,80,72,100,90,125,140,170,0
zx_win:
    xor a
    ld (zx_game_active),a
    call zx_cls
    ld hl,$0203
    ld (zx_cursor),hl
    ld hl,zx_won
    call zx_print
    call zx_crowns ; Vítězství zachová všech šest korunek včetně paprsků.
    call zx_release
    call zx_music_start
    ; Přehrávač vrací EI; před novou hrou ztišit výstup beeperu.
    xor a
    out ($fe),a
    jp zx_restart
zx_release:
    call zx_wait_frame
    call zx_any_key
    jr nz,zx_release
    ret
zx_end_wait:
    call zx_wait_frame
    call zx_menu_key
    jr nz,zx_end_wait
    jp zx_restart
zx_title:
    defb "HL",CZ_I,"PA",13,"ZX SPECTRUM 48K",13,"ATARIBABY 2026",0 ; HLÍPA
zx_help:
    defb "KASUHA SOFTWARE",13,"KAREL ",CZ_S,"UHAJDA / TOM",CZ_A,CZ_S," ",CZ_S,"VEC",13 ; KAREL ŠUHAJDA / TOMÁŠ ŠVEC
    defb ZX_PLOXON_TL,ZX_PLOXON_TR,13,ZX_PLOXON_BL,ZX_PLOXON_BR
    defb " ZNI",CZ_C," ",CZ_S,"EST PLOXON",CZ_U_KROUZEK,".",13 ; ZNIČ ŠEST PLOXONŮ.
    defb ZX_FALMON_TL,ZX_FALMON_TR,13,ZX_FALMON_BL,ZX_FALMON_BR
    defb " VYH",CZ_Y,"BEJ SE FALMON",CZ_U_KROUZEK,"M.",13,13 ; VYHÝBEJ SE FALMONŮM.
    defb "Q  VLEVO NAHORU",13,"A  VPRAVO DOL",CZ_U_KROUZEK,13 ; A  VPRAVO DOLŮ
    defb "O  VLEVO DOL",CZ_U_KROUZEK,13,"P  VPRAVO NAHORU",13,13 ; O  VLEVO DOLŮ
    defb "TAK",CZ_E," KURZOROV",CZ_E," 5 6 7 8",13 ; TAKÉ KURZOROVÉ 5 6 7 8
    defb "1 MENU",13,13
    defb "0 NEBO ENTER: START",0
zx_joy_label: defb "J KEMPSTON: ",0
zx_joy_off: defb "VYP",0
zx_joy_on: defb "ZAP",0
zx_won:
    defb "        BLAHOP",CZ_R,"EJI!",13,13 ; BLAHOPŘEJI! uprostřed 32 sloupců.
    defb "--------------------------",13,13
    defb "V",CZ_A,CZ_S," OBDIVUHODN",CZ_Y," V",CZ_Y,"KON",13 ; VÁŠ OBDIVUHODNÝ VÝKON
    defb "BUDE NAV",CZ_E_HACEK,"KY ZAZNAMEN",CZ_A,"N",13 ; BUDE NAVĚKY ZAZNAMENÁN
    defb "DO MOLEKUL",CZ_A,"RN",CZ_I," PAM",CZ_E_HACEK,"TI",13 ; DO MOLEKULÁRNÍ PAMĚTI
    defb "CEL",CZ_E,"HO HL",CZ_I,"P",CZ_I,"HO N",CZ_A,"RODA",13 ; CELÉHO HLÍPÍHO NÁRODA
    defb "A VA",CZ_S,"E T",CZ_E_HACEK,"LO PO SMRTI",13 ; A VAŠE TĚLO PO SMRTI
    defb "NALITO DO K",CZ_R,"I",CZ_S,CZ_T,CZ_A,"LOV",CZ_E,13 ; NALITO DO KŘIŠŤÁLOVÉ
    defb "LAHVE",13,13
    defb CZ_S,"EST PLOXON",CZ_U_KROUZEK," JE ZNI",CZ_C,"ENO.",13,13 ; ŠEST PLOXONŮ JE ZNIČENO.
    defb "0 NEBO ENTER: NOV",CZ_A," HRA",0 ; 0 NEBO ENTER: NOVÁ HRA
zx_lost:
    defb "         KONEC HRY",13,"--------------------------",13,13
    defb "HL",CZ_I,"PA NYN",CZ_I," NAV",CZ_S,"T",CZ_I,"VILA",13,0 ; HLÍPA NYNÍ NAVŠTÍVILA

; Původní bitmapa navštívených místností: dva bloky po 128 bitech.
zx_count_visits:
    ld de,0
    ld hl,$f070
    call zx_count_block
    ld hl,$f0b0
zx_count_block:
    ld b,16
zx_count_byte:
    ld a,(hl)
    inc hl
zx_count_bit:
    add a,a
    jr nc,zx_count_skip
    inc de
zx_count_skip:
    jr nz,zx_count_bit
    djnz zx_count_byte
    ret
zx_results:
    call zx_count_visits
    ld (zx_visits),de
    ; PMD procento zaokrouhluje nahoru: ceil(pocet * 100 / 256).
    ex de,hl
    add hl,hl
    add hl,hl
    ld b,h
    ld c,l
    add hl,hl
    add hl,bc
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,bc
    ld a,l
    add a,255
    ld a,h
    adc a,0
    ld (zx_percent),a
    ld hl,$0203
    ld (zx_cursor),hl
    ld hl,zx_lost
    call zx_print
    ld de,(zx_visits)
    ld a,d
    or a
    jr z,zx_visit_byte
    ld hl,zx_all_rooms
    call zx_print
    jr zx_visit_suffix
zx_visit_byte:
    ld a,e
    call zx_number
zx_visit_suffix:
    ld hl,zx_rooms_suffix
    ld a,(zx_visits+1)
    or a
    jr nz,zx_visit_text
    ld a,(zx_visits)
    cp 1
    jr z,zx_visit_one
    cp 2
    jr c,zx_visit_text
    cp 5
    jr nc,zx_visit_text
    ld hl,zx_few_rooms
    jr zx_visit_text
zx_visit_one:
    ld hl,zx_one_room
zx_visit_text:
    call zx_print
    ld a,(zx_percent)
    call zx_number
    ld hl,zx_percent_suffix
    call zx_print
    ld hl,$0803
    ld (zx_cursor),hl
    ld a,($f17d)
    ld b,6
    ld c,0
zx_result_count:
    rrca
    jr nc,zx_result_next
    inc c
zx_result_next:
    djnz zx_result_count
    ld a,c
    ld (zx_collected),a
    or a
    ld hl,zx_no_crowns
    jr z,zx_result_crowns
    ld hl,zx_found_crowns
    call zx_print
    ld a,(zx_collected)
    call zx_number
    ld hl,zx_crowns_suffix
zx_result_crowns:
    call zx_print
    ld hl,$0b03
    ld (zx_cursor),hl
    ld hl,zx_rating_label
    call zx_print
    ld a,(zx_visits+1)
    or a
    ld a,4
    jr nz,zx_rating_base
    ld a,(zx_visits)
    rlca
    rlca
    rlca
    and 7
    inc a
    rra
zx_rating_base:
    ld b,a
    ld a,(zx_collected)
    add a,b
    cp 8
    jr c,zx_rating_select
    ld a,8
zx_rating_select:
    ld b,a
    ld a,($f1f3)
    or a
    ld a,b
    jr z,zx_rating_table
    ld a,8
zx_rating_table:
    add a,a
    ld l,a
    ld h,0
    ld de,zx_ratings
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ex de,hl
    call zx_print
    ld hl,$1103
    ld (zx_cursor),hl
    ld hl,zx_again
    jp zx_print
; Číslo 0–255 bez úvodních nul pro závěrečné statistiky.
zx_number:
    ld e,48
    ld b,100
    call zx_digit
    ld b,10
    call zx_digit
    add a,48
    jp zx_text
zx_digit:
    ld c,0
zx_digit_loop:
    sub b
    jr c,zx_digit_end
    inc c
    jr zx_digit_loop
zx_digit_end:
    add a,b
    push af
    ld a,c
    add a,48
    cp e
    jr z,zx_digit_skip
    ld e,0
    call zx_text
zx_digit_skip:
    pop af
    ret
zx_visits: defw 0
zx_percent: defb 0
zx_collected: defb 0
zx_all_rooms: defb "256",0
zx_rooms_suffix: defb " M",CZ_I,"STNOST",CZ_I," = ",0 ;  MÍSTNOSTÍ =
zx_few_rooms: defb " M",CZ_I,"STNOSTI = ",0 ; MÍSTNOSTI
zx_one_room: defb " M",CZ_I,"STNOST = ",0 ;  MÍSTNOST =
zx_percent_suffix: defb "%.",0
zx_no_crowns: defb "NENA",CZ_S,"LA ",CZ_Z,CZ_A,"DNOU KORUNKU.",0 ; NENAŠLA ŽÁDNOU KORUNKU.
zx_found_crowns: defb "SEBRAN",CZ_E," KORUNKY: ",0 ; SEBRANÉ KORUNKY:
zx_crowns_suffix: defb "/6",0
zx_rating_label: defb "JEJ",CZ_I," V",CZ_Y,"KON HODNOT",CZ_I,"M JAKO",13,13,0 ; JEJÍ VÝKON HODNOTÍM JAKO
zx_again: defb "0 NEBO ENTER: NOV",CZ_A," HRA",0 ; 0 NEBO ENTER: NOVÁ HRA
zx_ratings:
    defw zx_rating0,zx_rating1,zx_rating2,zx_rating3,zx_rating4
    defw zx_rating5,zx_rating6,zx_rating7,zx_rating8
zx_rating0: defb "NAPROSTO NEMO",CZ_Z,"N",CZ_Y,0 ; NAPROSTO NEMOŽNÝ
zx_rating1: defb "VELMI ",CZ_S,"PATN",CZ_Y,0 ; VELMI ŠPATNÝ
zx_rating2: defb CZ_S,"PATN",CZ_Y,0 ; ŠPATNÝ
zx_rating3: defb "HOR",CZ_S,CZ_I," PR",CZ_U_KROUZEK,"M",CZ_E_HACEK,"R",0 ; HORŠÍ PRŮMĚR
zx_rating4: defb "PR",CZ_U_KROUZEK,"M",CZ_E_HACEK,"RN",CZ_Y,0 ; PRŮMĚRNÝ
zx_rating5: defb "LEP",CZ_S,CZ_I," PR",CZ_U_KROUZEK,"M",CZ_E_HACEK,"R",0 ; LEPŠÍ PRŮMĚR
zx_rating6: defb "DOBR",CZ_Y,0 ; DOBRÝ
zx_rating7: defb "VELMI DOBR",CZ_Y,0 ; VELMI DOBRÝ
zx_rating8: defb "VYNIKAJ",CZ_I,"C",CZ_I,0 ; VYNIKAJÍCÍ

    include "czech_font.asm"
    include "menu_icons.asm"
zx_native_end:
