"""Hraní sestavené hry klávesami, checkpointy a záznam pro opakování průchodu.

Na rozdíl od cílených regresí nemění polohu, životy ani herní příznaky.
Pro hledání cesty lze obnovit pouze celou dříve dosaženou paměť a registry.
"""
import heapq
import itertools
import json
import pickle
import sys
import time
from collections import deque, defaultdict
from pathlib import Path

import skoolkit
from runtime import Machine, BUILD, ROOT

CARDINAL = {'N': 'O', 'S': 'P', 'E': 'Q', 'W': 'A'}


class Player(Machine):
    def __init__(self, contended=False):
        super().__init__()
        self.border = 0
        cpu = skoolkit.CCMIOSimulator if contended else skoolkit.CSimulator
        if cpu is None:
            raise RuntimeError('Průchod vyžaduje rychlé C jádro SkoolKitu.')
        self.sim = cpu(self.memory, registers={'PC': self.labels['zx_boot']},
                       config={'fast_djnz': False, 'fast_ldir': False})
        self.sim.set_tracer(self)
        self.memory = self.sim.memory
        self.r = self.sim.registers
        self.actions = []

    def until_tick(self, budget=35000000):
        reason, _ = self.sim.trace(self.r[24], self.labels['zx_tick'], 6000000,
                                   self.r[25]+budget, True, None, None, None, None, None)
        return reason == 3

    def boot(self):
        self.keys = {'0'}
        assert self.until_tick()
        self.keys = set()

    def frame(self, key=''):
        self.keys = {key} if key else set()
        live = self.until_tick(3500000)
        self.actions.append(key)
        return live and self.memory[0xf1f4] > 0

    def snapshot(self):
        return bytes(self.memory), self.r[:], len(self.actions)

    def restore(self, snapshot):
        memory, registers, length = snapshot
        self.memory[:] = memory
        self.r[:] = registers
        self.actions = self.actions[:length]

    def save(self, name):
        folder = BUILD / 'walkthrough'
        folder.mkdir(exist_ok=True)
        with (folder / f'{name}.state').open('wb') as stream:
            pickle.dump((self.snapshot(), self.actions), stream)
        (folder / f'{name}.json').write_text(json.dumps({
            'actions': self.actions, 'position': self.position(),
            'health': self.memory[0xf1f4], 'crowns': self.memory[0xf17d],
            'tstates': self.r[25]}, indent=2))
        self.screenshot(folder / f'{name}.png')

    def load(self, name):
        with (BUILD / 'walkthrough' / f'{name}.state').open('rb') as stream:
            snapshot, actions = pickle.load(stream)
        self.actions = actions
        self.restore(snapshot)

    def cell(self, x, y, z):
        return self.memory[0xeff0 - (y*8+x)*64 + z]

    def floor_plan(self):
        return [[max((z for z in range(15) if self.cell(x,y,z)), default=-1)
                 for x in range(8)] for y in range(8)]

    def state_key(self):
        return (self.position(), self.memory[0xf17d],
                bytes(self.memory[0xf139:0xf13c]), self.memory[0xf170],
                self.memory[0xf0fb], self.memory[0xf1f2],
                bytes(self.memory[0xf234:0xf238]), self.memory[0xf13f])

    def find_room(self, target, max_nodes=15000, chunk=4):
        distances = self.exit_distances(target)
        print('Exit estimate',target,distances.get(self.position()[1:4]),'cells',len(distances),flush=True)
        return self.search(lambda:self.position()[0]==target,str(target),max_nodes,chunk,distances)

    def exit_distances(self, target, point=None):
        """Pouze heuristika nad přečtenými kolizemi; pohyb vždy provádí Z80."""
        room = self.position()[0]
        exits = self.memory[0x8018+room*8:0x801e+room*8]
        nodes = {(x,y,z) for x in range(8) for y in range(8) for z in range(2,15)
                 if not self.cell(x,y,z) and self.cell(x,y,z-1)}
        reverse = defaultdict(list)
        goals = {point} if point else set()
        for x,y,z in nodes:
            if z == 14 and exits[4] == target: goals.add((x,y,z))
            for dx,dy,side in [(0,1,0),(0,-1,1),(1,0,2),(-1,0,3)]:
                nx,ny,nz = x+dx,y+dy,z
                if not 0<=nx<8 or not 0<=ny<8:
                    if exits[side] == target:goals.add((x,y,z))
                    continue
                if self.cell(nx,ny,nz):nz+=1
                if nz>14 or self.cell(nx,ny,nz):continue
                while nz>=2 and not self.cell(nx,ny,nz-1):nz-=1
                if nz<2:
                    if exits[5] == target:goals.add((x,y,z))
                elif (nx,ny,nz) in nodes:
                    reverse[nx,ny,nz].append((x,y,z))
        for p in range(0x9f5c,0xa03d,5):
            src,xy,z,dest,uv = self.memory[p:p+5]
            if src==room and dest==target:goals.add((xy>>4,xy&15,z&15))
        distances={p:0 for p in goals}
        queue=deque(goals)
        while queue:
            p=queue.popleft()
            for prev in reverse[p]:
                if prev not in distances:
                    distances[prev]=distances[p]+1
                    queue.append(prev)
        return distances

    def find_crown(self, bit, max_nodes=15000):
        room,xy,z=self.memory[0x8004+bit*3:0x8007+bit*3]
        assert room==self.position()[0]
        point=(xy>>4,xy&15,z-1)
        if not self.search(lambda:self.position()[1:4]==point,f'under-crown-{bit+1}',
                           max_nodes,4,self.exit_distances(None,point)):
            return False
        for _ in range(180):
            self.frame()
            if self.memory[0xf17d]&(1<<bit):
                self.frame();self.frame()
                print('Collected',bit+1,'mask',self.memory[0xf17d],flush=True)
                return True
        return False

    def search(self, goal, description, max_nodes=15000, chunk=4, distances=None):
        original = self.snapshot()
        prefix = self.actions[:]
        origin = self.position()[0]
        serial = itertools.count()
        queue = [(0, next(serial), original, ())]
        best = {}
        count = 0
        started = time.monotonic()
        while queue and count < max_nodes:
            cost, _, snapshot, path = heapq.heappop(queue)
            self.actions = prefix + list(path)
            self.restore(snapshot)
            count += 1
            for key in ('Q','A','O','P',''):
                self.actions = prefix + list(path)
                self.restore(snapshot)
                advanced = []
                for _ in range(chunk):
                    alive = self.frame(key)
                    advanced.append(key)
                    if goal():
                        print('Reached', description, self.position(), 'health',self.memory[0xf1f4],
                              'frames',len(self.actions),'nodes',count,'seconds',round(time.monotonic()-started,2),flush=True)
                        return True
                    if not alive:
                        break
                    if self.position()[0] != origin:
                        break
                if not alive or self.position()[0] != origin:
                    continue
                state = self.state_key()
                new_path = path + tuple(advanced)
                new_cost = len(new_path) + (31-self.memory[0xf1f4])*20
                if best.get(state, 10**9) <= new_cost:
                    continue
                best[state] = new_cost
                heuristic = 4*distances.get(self.position()[1:4],50) if distances else 0
                heapq.heappush(queue,(new_cost+heuristic,next(serial),self.snapshot(),new_path))
            if count%2000==0:
                print('Search',origin,'->',description,'nodes',count,'queue',len(queue),flush=True)
        self.actions = prefix
        self.restore(original)
        print('No path',origin,description,'nodes',count,'seconds',round(time.monotonic()-started,2),flush=True)
        return False


if __name__ == '__main__':
    m = Player()
    if len(sys.argv)>1:
        m.load(sys.argv[1])
    else:
        m.boot()
    print('Position',m.position(),'health',m.memory[0xf1f4],flush=True)
    print('Floor heights',*m.floor_plan(),sep='\n',flush=True)
    for room in map(int,sys.argv[2:]):
        if not m.find_room(room):
            break
        m.save(f'room-{room}')
    if len(sys.argv)==1:
        m.save('start')
