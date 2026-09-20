"""Rozbor statické mapy v oddělené pracovní paměti; nezasahuje do rozehrané hry.

Heuristické cesty vždy musí následně projít skutečným Z80 ovládáním.
"""
from collections import deque
import json
from walkthrough import Player, BUILD


def extract_map():
    scratch=Player();scratch.boot()
    rooms=[]
    for room in range(256):
        scratch.memory[0xf1f0]=room
        scratch.memory[0xffee:0xfff0]=bytes([0,0x5b])
        scratch.r[12]=0xffee;scratch.r[6]=0xb7;scratch.r[7]=0x45
        reason,_=scratch.sim.trace(scratch.labels['pmd_5745'],0x5b00,600000,0,False,None,None,None,None,None)
        assert reason==3
        rooms.append({'exits':list(scratch.memory[0x8018+room*8:0x801e+room*8]),
                      'cells':[scratch.cell(x,y,z) for y in range(8) for x in range(8) for z in range(16)]})
    channels=[list(scratch.memory[p:p+5]) for p in range(0x9f5c,0xa03d,5)]
    crowns=[list(scratch.memory[p:p+3]) for p in range(0x8004,0x8016,3)]
    result={'rooms':rooms,'channels':channels,'crowns':crowns}
    (BUILD/'walkthrough/map.json').write_text(json.dumps(result))
    return result


class Map:
    def __init__(self):
        path=BUILD/'walkthrough/map.json'
        self.data=json.loads(path.read_text()) if path.exists() else extract_map()
        self.rooms=self.data['rooms']
        self.portals={(r,xy>>4,xy&15,z&15):(d,uv>>4,uv&15,z>>4)
                      for r,xy,z,d,uv in self.data['channels']}

    def cell(self,r,x,y,z):
        if not 0<=z<16:return 0
        return self.rooms[r]['cells'][(y*8+x)*16+z]

    def settle(self,p):
        seen=set()
        while p not in seen:
            seen.add(p)
            r,x,y,z=p
            if z<2:
                p=(self.rooms[r]['exits'][5],x,y,z+12)
            elif self.cell(r,x,y,z):
                return None
            elif not self.cell(r,x,y,z-1):
                p=(r,x,y,z-1)
            elif z==14:
                p=(self.rooms[r]['exits'][4],x,y,2)
            elif p in self.portals:
                p=self.portals[p]
            else:
                return p
        return None

    def neighbors(self,p):
        r,x,y,z=p
        for key,dx,dy,side in [('Q',0,1,0),('A',0,-1,1),('P',1,0,2),('O',-1,0,3)]:
            nx,ny,nz=x+dx,y+dy,z
            if not 0<=nx<8 or not 0<=ny<8:
                q=self.settle((self.rooms[r]['exits'][side],nx%8,ny%8,z))
            else:
                if self.cell(r,nx,ny,nz):
                    nz+=1
                    if nz>14 or self.cell(r,nx,ny,nz) or self.cell(r,x,y,nz):continue
                q=self.settle((r,nx,ny,nz))
            if q is not None:
                yield key,q

    def route(self,start,goal,blocked=(),forbidden_nodes=()):
        start=self.settle(start)
        if start is None:return None
        queue=deque([start]);prev={start:None};keys={}
        while queue:
            p=queue.popleft()
            if p==goal:
                result=[]
                while prev[p] is not None:
                    result.append((keys[p],p));p=prev[p]
                return list(reversed(result))
            for key,q in self.neighbors(p):
                if q in forbidden_nodes or (p,key,q) in blocked or q in prev:continue
                prev[q]=p;keys[q]=key;queue.append(q)
        return None


if __name__=='__main__':
    import sys
    m=Player();m.load(sys.argv[1]);world=Map()
    for r,xy,z in world.data['crowns']:
        route=world.route(m.position()[:4],(r,xy>>4,xy&15,z-1))
        summary=[]
        for key,p in route or []:
            if not summary or summary[-1]!=p[0]:summary.append(p[0])
        print('Crown',r,'moves',len(route) if route else None,'rooms',summary,flush=True)
