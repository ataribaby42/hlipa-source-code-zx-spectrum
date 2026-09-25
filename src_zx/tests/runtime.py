"""Vykonává skutečný sestavený Z80 kód s 48K ROM, ULA klávesnicí a IRQ."""
from pathlib import Path
from collections import deque,Counter
import re,sys
import skoolkit
from skoolkit.simulator import Simulator
from skoolkit.traceutils import disassemble
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
BUILD=ROOT/'src_zx/build'

def symbols():
    return {m[1]:int(m[2],16) for m in re.finditer(r'^(\w+)\s+= \$([0-9A-F]+)',(BUILD/'HLIPA.map').read_text(),re.M)}

class Machine:
    frame_duration=69888
    int_active=32
    def __init__(self,contended=False):
        self.labels=symbols(); self.keys=set();self.ports=Counter();self.audio=[];self.joystick=255
        self.memory=[0]*65536
        self.memory[:16384]=(Path(skoolkit.__file__).parent/'resources/48.rom').read_bytes()
        b=(BUILD/'HLIPA.bin').read_bytes();self.memory[0x5b00:0x5b00+len(b)]=b
        from skoolkit.cmiosimulator import CMIOSimulator
        cpu=CMIOSimulator if contended else Simulator
        self.sim=cpu(self.memory,registers={'PC':self.labels['zx_boot']},config={'fast_djnz':False,'fast_ldir':False})
        self.sim.set_tracer(self);self.r=self.sim.registers
        self.recent=deque(maxlen=16);self.coverage=set();self.interrupts=0
    def read_port(self,r,port,*args):
        self.ports[('in',port&255)]+=1
        if port&255==31:return self.joystick
        if port&1:return 255
        rows=('CS','ASDFG','QWERT','12345','09876','POIUY','ELKJH',' SMNB')
        value=255
        for row,chars in enumerate(rows):
            if not port&(1<<(row+8)):
                for bit,c in enumerate(chars):
                    if c in self.keys:value &=~(1<<bit)
        return value
    def write_port(self,r,port,value,*args):
        self.ports[('out',port&255)]+=1
        if port&255==254:self.audio.append((r[25],value))
    def step(self):
        pc=self.r[24];self.coverage.add(pc);self.recent.append(pc)
        if not (0x5b00<=pc<0x5c00 or
                self.labels['pmd_code_start']<=pc<self.labels['pmd_code_end'] or
                self.labels['zx_boot']<=pc<self.labels['zx_native_end'] or
                self.labels['zx_music_start']<=pc<self.labels['zx_music_code_end']):
            raise AssertionError('PC mimo kód: '+str([(hex(p),disassemble(self.memory,p)[0]) for p in self.recent]))
        self.sim.run()
        if self.r[26] and self.r[25]%self.frame_duration<self.int_active:
            self.sim.accept_interrupt(self.r,self.memory,pc);self.interrupts+=1
    def run_until(self,predicate,limit=6000000):
        for i in range(limit):
            if predicate():return i
            self.step()
        raise AssertionError(f'Limit instrukcí: PC={self.r[24]:04X}, stav={self.position()}')
    def at(self,label):return self.r[24]==self.labels[label]
    def position(self):return (self.memory[0xf1f0],*self.memory[0xf135:0xf139])
    def steps(self):
        p=self.labels['zx_step_count'];return self.memory[p]+256*self.memory[p+1]
    def screenshot(self,path):
        im=Image.new('RGB',(256,192))
        for y in range(192):
            for x in range(256):
                a=0x4000+(y&192)*32+(y&7)*256+(y&56)*4+x//8
                v=self.memory[a]&(128>>(x&7))
                im.putpixel((x,y),(224,224,224) if v else (0,0,0))
        im.resize((768,576),Image.Resampling.NEAREST).save(path)

if __name__=='__main__':
    m=Machine();m.run_until(lambda:m.at('zx_menu_wait'));m.screenshot(BUILD/'zx-menu.png')
    m.keys={'0'};m.run_until(lambda:m.at('zx_tick'));m.keys=set();m.screenshot(BUILD/'zx-game.png')
    start=m.r[25];m.run_until(lambda:m.steps()>=50);m.screenshot(BUILD/'zx-game-50.png')
    print('50 kroků',m.position(),'čas', (m.r[25]-start)/3500000,'IRQ',m.interrupts)
