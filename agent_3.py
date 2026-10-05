import time
from collections import deque

def check_corner_trap(boxes, walls, goals):
    # print("Checking possible box traps:", boxes)
    for b in boxes:
        if b in goals: 
            continue
            
        bx, by = b
        up = (bx, by-1) in walls
        down = (bx, by+1) in walls
        left = (bx-1, by) in walls
        right = (bx+1, by) in walls
        
        if (up or down) and (left or right):
            return True
            
        # Check if the box is stuck along a horizontal edge
        if up or down:
            left_dead = False
            cx = bx - 1
            while True:
                if (cx, by) in goals:
                    break
                if (cx, by) in walls:
                    left_dead = True
                    break
                if up and (cx, by-1) not in walls:
                    break
                if down and (cx, by+1) not in walls:
                    break
                cx -= 1
                
            right_dead = False
            cx = bx + 1
            while True:
                if (cx, by) in goals:
                    break
                if (cx, by) in walls:
                    right_dead = True
                    break
                if up and (cx, by-1) not in walls:
                    break
                if down and (cx, by+1) not in walls:
                    break
                cx += 1
                
            if left_dead and right_dead:
                return True
                
        # Check the same problem along a vertical edge
        if left or right:
            up_dead = False
            cy = by - 1
            while True:
                if (bx, cy) in goals:
                    break
                if (bx, cy) in walls:
                    up_dead = True
                    break
                if left and (bx-1, cy) not in walls:
                    break
                if right and (bx+1, cy) not in walls:
                    break
                cy -= 1
                
            down_dead = False
            cy = by + 1
            while True:
                if (bx, cy) in goals:
                    break
                if (bx, cy) in walls:
                    down_dead = True
                    break
                if left and (bx-1, cy) not in walls:
                    break
                if right and (bx+1, cy) not in walls:
                    break
                cy += 1
                
            if up_dead and down_dead:
                return True
                
    return False

cached_plan = []
last_known_boxes = None

def get_action(my_pos, other_pos, boxes, targets, walls):
    # print("Agent 3 state:", my_pos, boxes)
    global cached_plan, last_known_boxes
    
    if last_known_boxes == boxes and cached_plan:
        next_move = cached_plan[0]
        dx, dy = 0, 0
        if next_move == 'N': dy = -1
        elif next_move == 'S': dy = 1
        elif next_move == 'W': dx = -1
        elif next_move == 'E': dx = 1
        
        nx, ny = my_pos[0] + dx, my_pos[1] + dy
        if (nx, ny) not in walls and (nx, ny) != other_pos:
            if (nx, ny) in boxes:
                nnx, nny = nx + dx, ny + dy
                if (nnx, nny) not in walls and (nnx, nny) not in boxes and (nnx, nny) != other_pos:
                    return cached_plan.pop(0)
            else:
                return cached_plan.pop(0)
                
    cached_plan = []
    # print("Cached plan invalid, starting a new search")
    t0 = time.perf_counter()
    
    initial = (my_pos, frozenset(boxes))
    q = deque([initial]) # Queue for states waiting to be checked
    
    came_from = dict()
    came_from[initial] = (None, None)
    
    explored = set()
    explored.add(initial)
    
    base_pts = len([b for b in boxes if b in targets])
    
    best_node = initial
    best_depth = -1
    depths = {initial: 0}
    
    while q:
        # Stop before the search takes too long
        if time.perf_counter() - t0 > 0.80:
            break
            
        state = q.popleft() # Take the oldest state first
        rob_pos, curr_bxs = state
        
        pts = len([b for b in curr_bxs if b in targets])
        if pts > base_pts:
            # Rebuild the path and return its first move
            n = state
            path = []
            while came_from[n][0] != initial:
                path.append(came_from[n][1])
                n = came_from[n][0]
                if n is None: break
            if n is not None:
                path.append(came_from[n][1])
                path.reverse()
                cached_plan = path[1:]
                last_known_boxes = boxes.copy()
                return path[0]
                
        dirs = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'W': (-1, 0)}
        for act in dirs:
            delta = dirs[act]
            new_rx = rob_pos[0] + delta[0]
            new_ry = rob_pos[1] + delta[1]
            
            if (new_rx, new_ry) in walls or (new_rx, new_ry) == other_pos:
                continue
                
            next_b = set(curr_bxs)
            if (new_rx, new_ry) in curr_bxs:
                push_x = new_rx + delta[0]
                push_y = new_ry + delta[1]
                
                if (push_x, push_y) in walls or (push_x, push_y) in curr_bxs or (push_x, push_y) == other_pos:
                    continue
                    
                next_b.remove((new_rx, new_ry))
                next_b.add((push_x, push_y))
                
                if check_corner_trap([(push_x, push_y)], walls, targets):
                    continue
                
            succ = ((new_rx, new_ry), frozenset(next_b))
            
            if succ not in explored:
                explored.add(succ)
                came_from[succ] = (state, act)
                
                new_depth = depths[state] + 1
                depths[succ] = new_depth
                if new_depth > best_depth:
                    best_depth = new_depth
                    best_node = succ
                    
                q.append(succ) # Add the new state to the queue
                
    if best_node != initial:
        n = best_node
        path = []
        while came_from[n][0] != initial:
            path.append(came_from[n][1])
            n = came_from[n][0]
            if n is None: break
        if n is not None:
            path.append(came_from[n][1])
            path.reverse()
            cached_plan = path[1:]
            last_known_boxes = boxes.copy()
            return path[0]
            
    return 'STAY'
