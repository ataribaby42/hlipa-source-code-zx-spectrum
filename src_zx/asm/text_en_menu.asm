; Anglické menu a závěrečné obrazovky. Název hry a jména autorů zůstávají původní.
zx_help:
    defb "KASUHA SOFTWARE",13,"KAREL ",CZ_S,"UHAJDA / TOM",CZ_A,CZ_S," ",CZ_S,"VEC",13
    defb ZX_PLOXON_TL,ZX_PLOXON_TR,13,ZX_PLOXON_BL,ZX_PLOXON_BR
    defb " DESTROY SIX PLOXONS.",13
    defb ZX_FALMON_TL,ZX_FALMON_TR,13,ZX_FALMON_BL,ZX_FALMON_BR
    defb " AVOID THE FALMONS.",13,13
    defb "Q  UP-LEFT",13,"A  DOWN-RIGHT",13
    defb "O  DOWN-LEFT",13,"P  UP-RIGHT",13,13
    defb "ALSO CURSOR KEYS 5 6 7 8",13
    defb "1 MENU",13,13
    defb "0 OR ENTER: START",0
zx_joy_label: defb "J KEMPSTON: ",0
zx_joy_off: defb "OFF",0
zx_joy_on: defb "ON ",0
zx_won:
    defb "     CONGRATULATIONS!",13,13
    defb "--------------------------",13,13
    defb "YOUR ADMIRABLE FEAT",13
    defb "WILL BE RECORDED FOREVER",13
    defb "IN THE MOLECULAR MEMORY",13
    defb "OF THE ENTIRE HL",CZ_I,"PA NATION",13
    defb "AND YOUR BODY WILL BE",13
    defb "POURED, AFTER DEATH, INTO",13
    defb "A CRYSTAL BOTTLE",13,13
    defb "SIX PLOXONS ARE DESTROYED.",13,13
    defb "0 OR ENTER: NEW GAME",0
zx_lost:
    defb "         GAME OVER",13,"--------------------------",13,13
    defb "HL",CZ_I,"PA HAS VISITED",13,0
