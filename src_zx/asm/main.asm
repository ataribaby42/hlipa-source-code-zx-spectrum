    org $5b00
program_start:
    jp zx_boot
    defs $5b-($-program_start),0
zx_irq:
    push af
    ld a,(zx_frames)
    inc a
    ld (zx_frames),a
    pop af
    ei
    reti
zx_frames: defb 0
zx_deadline: defb 0
zx_cursor: defw 0
zx_game_active: defb 0
zx_step_count: defw 0
zx_kempston: defb 0
zx_position_valid: defb 0
zx_last_position: defs 3,0
zx_last_room: defb 0
zx_last_motion_state: defb 0
zx_last_crowns: defb 0
    defs $500-($-program_start),0
    include "game.asm"
    include "spectrum.asm"
    ; Za kompaktním kódem je souvislá rezerva až k pracovním frontám.
    defs $6a9d-($-program_start),0
    defs $263,0 ; pracovní masky a fronty $C59D–$C7FF
    defs $1800,0 ; pracovní obraz $C800–$DFFF
    defs $1400,0 ; kolize a stav hry $E000–$F3FF
zx_extension_space:
zx_font:
    incbin "src_zx/data/font_cz.bin"
zx_font_end:
    ; Přehrávač, skladba a pracovní bajty v původní souvislé rezervě.
    include "music.asm"
    defs $a300-($-program_start),0
    defs 257,$5b
    defs $a4f0-($-program_start),0
