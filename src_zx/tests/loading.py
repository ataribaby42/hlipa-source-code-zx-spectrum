"""Načtení distribuce: BASIC a ROM loader TAP, následně start hry z TAP i SNA."""
from runtime import Machine, ROOT, BUILD, symbols
from skoolkit.snapshot import Snapshot
from skoolkit.tap2sna import main as tap2sna
from skoolkit.simutils import from_snapshot
from skoolkit.simulator import Simulator
from skoolkit.pagingtracer import Memory
import argparse,json
from contextlib import chdir


class LoadedMachine(Machine):
    """Pokračuje se skutečnou ROM, stránkami RAM a registry načteného stroje."""
    def __init__(self,snapshot,variant='HLIPA'):
        super().__init__(variant=variant)
        self.sim=from_snapshot(Simulator,snapshot,config={'fast_djnz':False,'fast_ldir':False})
        self.sim.set_tracer(self)
        self.memory=self.sim.memory
        self.r=self.sim.registers
        if isinstance(self.memory,Memory):
            self.frame_duration=70908
            self.int_active=36

    def position(self):
        return (self.memory[0xf1f0],*(self.memory[a] for a in range(0xf135,0xf139)))

    def write_port(self,r,port,value,*args):
        super().write_port(r,port,value,*args)
        if isinstance(self.memory,Memory) and port&0x8002==0 and not self.memory.o7ffd&32:
            self.memory.out7ffd(value)


def verify_loading(fast_load=True,machine='48',variant='HLIPA'):
    suffix=('-en' if variant=='HLIPA_EN' else '')+('-128' if machine=='128' else '')+('' if fast_load else '-sampled')
    picture = BUILD / f'loading-picture{suffix}.z80'
    converted = BUILD / f'from-tape{suffix}.z80'
    labels=symbols(variant)
    entry=labels['zx_boot']
    picture_ready=0x0556  # ROM LD-BYTES před čtením další hlavičky.
    expected_screen=(ROOT/'src_zx/data/loading.scr').read_bytes()
    # SkoolKit vykládá dvojtečku v absolutní Windows cestě jako URL schéma.
    with chdir(ROOT):
        # První běh ukončí pásku po obrázku. Adresu ROM smí zachytit až po
        # konci pásky, jinak by skončil už při načítání samotného BASICu.
        for stop,path,extra in [(picture_ready,picture,['--tape-stop','5',
                                '--sim-load-config','finish-tape=1']),
                               (entry,converted,[])]:
            tap2sna(extra+['--start',str(stop),'--sim-load-config',f'fast-load={int(fast_load)}',
                     '--sim-load-config',f'machine={machine}',
                     f'output_zx/{variant}.tap',str(path)])
    # 128K se načítá volbou Tape Loader z úvodního menu (ENTER), nikoli
    # přepnutím do 48 BASICu. Obrázek musí přežít celý přenos hlavního kódu,
    # včetně atributů a bez přepsání názvem dalšího bloku pásky.
    for path,pc in [(picture,picture_ready),(converted,entry)]:
        snapshot=Snapshot.get(str(path))
        assert snapshot.pc==pc
        assert snapshot.border==0
        assert bytes(snapshot.ram()[:6912])==expected_screen, ('Poškozený obrázek',path.name)
        ram=snapshot.ram()
        assert 0x5c00<snapshot.sp<0x6000, ('Zásobník ROM zasahuje do hry',snapshot.sp)
        assert bytes(ram[23730-0x4000:23732-0x4000])==b'\xff\x5f'  # RAMTOP
        assert bytes(ram[23739-0x4000:23741-0x4000])==b'\x6f\x09'
        if machine=='128':
            assert snapshot.machine=='128K'
            assert snapshot.out7ffd==0x10, ('Jiná ROM nebo stránka RAM',snapshot.out7ffd)
    loaded=Snapshot.get(str(converted))
    image=(BUILD/f'{variant}.bin').read_bytes()[0x500:labels['zx_native_end']-0x5b00]
    assert bytes(loaded.ram()[0x2000:0x2000+len(image)])==image
    font=(ROOT/'src_zx/data/font_cz.bin').read_bytes()
    font_start=labels['zx_font']
    assert bytes(loaded.ram()[font_start-0x4000:font_start-0x4000+768])==font
    music_start=labels['zx_music_start']
    music_end=labels['zx_music_end']
    music=(BUILD/f'{variant}.bin').read_bytes()[music_start-0x5b00:music_end-0x5b00]
    assert bytes(loaded.ram()[music_start-0x4000:music_end-0x4000])==music
    preview=Machine();preview.memory[16384:]=loaded.ram()
    preview.screenshot(BUILD/f'loading-screen{suffix}.png')
    result = {'variant':variant,'machine':machine+'K','start_mode':'128K Tape Loader menu' if machine=='128' else '48K BASIC',
              'loading_screen':{'bytes':6912,'before_code_load':True,
                               'after_code_load':True,'black_border':True},
              'fast_load':fast_load,'loader':'BASIC','compressed':False,
              'rom_stack_below_code':True,'screen_channel_suppressed':True}
    for name, path in [('tap', converted), ('sna', ROOT / f'output_zx/{variant}.sna')]:
        snapshot = Snapshot.get(str(path))
        assert snapshot.pc == entry
        m = LoadedMachine(snapshot,variant=variant)
        m.run_until(lambda: m.at('zx_menu_wait'))
        assert bytes(m.memory[a] for a in range(font_start,font_start+768))==font
        assert bytes(m.memory[a] for a in range(music_start,music_end))==music
        m.keys = {'0'}
        m.run_until(lambda: m.at('zx_tick'))
        m.keys = set()
        m.run_until(lambda: m.steps() >= 50)
        assert m.memory[0xf1f0] == 0
        # Ještě pohyb a návrat do menu: IM2 už používá původní pracovní oblast
        # ROM 128K, ale během hry se nesmí znovu spustit stará obsluha ROM.
        m.keys={'P'};m.run_until(lambda:m.steps()>=63)
        assert m.position()[1]!=3
        m.keys={'1'};m.run_until(lambda:m.at('zx_menu_wait'))
        m.keys={'0'};m.run_until(lambda:m.at('zx_tick'))
        restarted_at=m.steps()
        m.keys=set();m.run_until(lambda:m.steps()>=restarted_at+5)
        assert m.position()[0]==0 and m.memory[0xf17d]==0
        assert m.memory[0xf1f4]==31
        assert bytes(m.memory[a] for a in range(font_start,font_start+768))==font
        # Hudba musí být přítomná i spustitelná z obou distribučních formátů.
        m.memory[0xf17d]=63
        m.run_until(lambda:m.at('zx_music_key'))
        audio_start=len(m.audio)
        m.step();m.run_until(lambda:m.at('zx_music_key'))
        assert any(value==16 for _,value in m.audio[audio_start:])
        m.keys={'E'};m.run_until(lambda:m.at('zx_tick'))
        assert m.memory[0xf17d]==0 and m.memory[0xf1f4]==31
        if isinstance(m.memory,Memory):assert m.memory.o7ffd==0x10
        result[name] = {'entry_pc': snapshot.pc, 'menu_and_game_started': True,
                        'game_steps_before_movement':50,'movement_and_restart':True,
                        'victory_music_and_restart':True,
                        'runtime_machine':snapshot.machine}
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-fast-load',action='store_true',help='Provést ROM čtení pulsů místo přímého nahrání bloku.')
    parser.add_argument('--machine',choices=('48','128'),default='48',help='128 načítá přímo z úvodního menu Tape Loader.')
    parser.add_argument('--english',action='store_true',help='Ověřit anglickou distribuci HLIPA_EN.')
    args=parser.parse_args()
    variant='HLIPA_EN' if args.english else 'HLIPA'
    report = verify_loading(fast_load=not args.no_fast_load,machine=args.machine,variant=variant)
    suffix=('-en' if args.english else '')+('-128' if args.machine=='128' else '')+('-sampled' if args.no_fast_load else '')
    (BUILD / f'loading-verification{suffix}.json').write_text(json.dumps(report, indent=2))
    print('Načtení obrázku, TAP a SNA prošlo. Přímé nahrání bloků:',not args.no_fast_load)
