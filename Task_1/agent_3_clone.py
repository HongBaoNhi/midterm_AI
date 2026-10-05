import time
from heapq import heappush, heappop

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
    # print("Agent 3 clone state:", my_pos, boxes)
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
    timer_start = time.perf_counter()
    
    root_node = (my_pos, frozenset(boxes))
    open_list = []
    heappush(open_list, (0, 0, root_node))
    
    # Keep the previous states so we can rebuild the move path
    history = {}
    history[root_node] = (None, None)
    
    g_vals = {root_node: 0}
    tie = 0
    
    # Count how many boxes are already on targets
    og_score = 0
    for b in boxes:
        if b in targets: og_score += 1
        
    best_node = root_node
    best_cost = -1
            
    while open_list:
        g, _, current_node = heappop(open_list)
        rob_pos, curr_bxs = current_node
        
        # Stop before the time limit becomes a problem
        if time.perf_counter() - timer_start > 0.80:
            break
            
        new_score = 0
        for b in curr_bxs:
            if b in targets: new_score += 1
            
        if new_score > og_score:
            node = current_node
            path = []
            while history[node][0] != root_node:
                path.append(history[node][1])
                node = history[node][0]
                if node is None: break
            if node is not None:
                path.append(history[node][1])
                path.reverse()
                cached_plan = path[1:]
                last_known_boxes = boxes.copy()
                return path[0]
                
        # Try each possible next move
        for a, (dx, dy) in [('N', (0, -1)), ('S', (0, 1)), ('E', (1, 0)), ('W', (-1, 0))]:
            new_rx, new_ry = rob_pos[0] + dx, rob_pos[1] + dy
            
            if (new_rx, new_ry) in walls: continue
            if (new_rx, new_ry) == other_pos: continue
                
            tmp_boxes = set(curr_bxs)
            if (new_rx, new_ry) in curr_bxs:
                push_x = new_rx + dx
                push_y = new_ry + dy
                
                if (push_x, push_y) in walls: continue
                if (push_x, push_y) in curr_bxs: continue
                if (push_x, push_y) == other_pos: continue
                
                tmp_boxes.remove((new_rx, new_ry))
                tmp_boxes.add((push_x, push_y))
                
                if check_corner_trap([(push_x, push_y)], walls, targets):
                    continue
                
            child = ((new_rx, new_ry), frozenset(tmp_boxes))
            new_cost = g_vals[current_node] + 1
            
            if child not in g_vals or new_cost < g_vals[child]:
                g_vals[child] = new_cost
                history[child] = (current_node, a)
                tie += 1
                heappush(open_list, (new_cost, tie, child))
                
                if new_cost > best_cost:
                    best_cost = new_cost
                    best_node = child
                
    if best_node != root_node:
        node = best_node
        path = []
        while history[node][0] != root_node:
            path.append(history[node][1])
            node = history[node][0]
            if node is None: break
        if node is not None:
            path.append(history[node][1])
            path.reverse()
            cached_plan = path[1:]
            last_known_boxes = boxes.copy()
            return path[0]
            
    return 'STAY'
