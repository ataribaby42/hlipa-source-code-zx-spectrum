; Ikonky menu: dvě bitmapy 16 × 16 rozdělené do čtyř znaků 8 × 8.
; Kódy $80–$87 jsou mimo 768bajtový font a používají stejný kreslič znaků.
; Ploxon: původní PMD sprite $1928, ořez na 12 × 13, beze změny pixelů.
; Falmon: PMD $15A8, ořez 19 × 18, zrcadlení a nejbližší bod na 16 × 16.
; Částice míří doprava, aby byla hlava čitelná u levého okraje menu.
    defc ZX_PLOXON_TL = $80
    defc ZX_PLOXON_TR = $81
    defc ZX_PLOXON_BL = $82
    defc ZX_PLOXON_BR = $83
    defc ZX_FALMON_TL = $84
    defc ZX_FALMON_TR = $85
    defc ZX_FALMON_BL = $86
    defc ZX_FALMON_BR = $87
    defc ZX_MENU_GLYPHS_END = $88

zx_menu_icons:
    defb $00,$00,$00,$06,$8f,$8f,$d9,$76
    defb $00,$00,$00,$00,$10,$10,$b0,$e0
    defb $6f,$7f,$7f,$3f,$3f,$26,$19,$06
    defb $60,$e0,$e0,$c0,$c0,$40,$80,$00
    defb $00,$00,$0f,$1c,$7f,$5b,$d7,$f3
    defb $02,$68,$4d,$b2,$53,$ec,$48,$22
    defb $ff,$ff,$df,$c7,$63,$33,$1f,$0f
    defb $94,$d0,$a8,$b0,$a0,$00,$c0,$00
