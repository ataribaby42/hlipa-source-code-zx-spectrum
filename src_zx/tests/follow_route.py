"""Zkouší odhadnutou cestu skutečnými klávesami; chybné odhady vyřadí."""
import sys
from walkthrough import Player
from map_routes import Map


def follow(checkpoint, bit):
    m=Player();m.load(checkpoint);world=Map()
    r,xy,z=world.data['crowns'][bit]
    goal=(r,xy>>4,xy&15,z-1)
    blocked=set();forbidden_nodes=set()
    initial=m.snapshot();initial_actions=m.actions[:]
    for attempt in range(100):
        route=world.route(m.position()[:4],goal,blocked,forbidden_nodes)
        if route is None:
            print('No static route',m.position(),goal,flush=True)
            return False
        print('Plan',attempt,'moves',len(route),'start',m.position(),flush=True)
        for key,target in route:
            origin=world.settle(m.position()[:4]);snapshot=m.snapshot()
            previous_room=m.position()[0]
            success=False
            for tick in range(400):
                if not m.frame(key):break
                if m.position()[:4]==target:
                    success=True;break
            if not success:
                print('Rejected',origin,key,target,'actual',m.position(),'ticks',tick,flush=True)
                if m.memory[0xf1f4]==0 and m.position()[0]!=goal[0]:
                    forbidden_nodes.add(m.position()[:4])
                    blocked.add((origin,key,target))
                    print('Avoid deadly position',m.position()[:4],flush=True)
                    m.actions=initial_actions[:];m.restore(initial)
                    break
                m.restore(snapshot)
                blocked.add((origin,key,target))
                break
            if previous_room!=m.position()[0]:
                print('Room',m.position(),'health',m.memory[0xf1f4],'frames',len(m.actions),flush=True)
                m.save('auto-progress')
        else:
            for _ in range(180):
                m.frame()
                if m.memory[0xf17d]&(1<<bit):
                    m.frame();m.frame();m.save('auto-crown-'+str(bit))
                    print('CROWN',bit,'mask',m.memory[0xf17d],'health',m.memory[0xf1f4],flush=True)
                    return True
            print('Crown was not collected',m.position(),flush=True)
            return False
    return False


if __name__=='__main__':
    assert follow(sys.argv[1],int(sys.argv[2]))
