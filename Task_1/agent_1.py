import time
import heapq

bfs_cache = {}
cached_targets = None

def precompute_bfs(targets, walls):
    # print("Precomputing BFS distances for", len(targets), "targets")
    global bfs_cache, cached_targets
    bfs_cache = {}
    cached_targets = targets
    
    for t in targets:
        # Start from the goal so box distances are easier to look up later
        queue = [(t, 0)]
        visited = {t}
        while queue:
            curr, dist = queue.pop(0)
            if curr not in bfs_cache or dist < bfs_cache[curr]:
                bfs_cache[curr] = dist
                
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                nx, ny = curr[0] + dx, curr[1] + dy
                if (nx, ny) not in walls and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append(((nx, ny), dist + 1))

# A box is not always stuck only when it is in an obvious corner
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
            # If both sides are blocked before a goal, the box cannot escape
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
            # Same check as above, but for a box against a side wall
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
    # print("Agent 1 state:", my_pos, boxes)
    global cached_plan, last_known_boxes, bfs_cache, cached_targets
    
    if cached_targets != targets:
        precompute_bfs(targets, walls)
    
    if last_known_boxes == boxes and cached_plan:
        # print("Trying cached move:", cached_plan[0])
        # Keep using the old plan if the boxes have not changed
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
    t_start = time.perf_counter()
    init_state = (my_pos, frozenset(boxes))
    
    # The state needs both positions because they affect which moves are allowed
    frontier = []
    heapq.heappush(frontier, (0, 0, init_state))
    
    came_from = dict()
    came_from[init_state] = (None, None)
    
    g_score = {init_state: 0}
    push_count = 0
    
    # This only tells us whether the search has made some progress
    base_score = sum(1 for box in boxes if box in targets)
    
    best_node = init_state
    best_h = float('inf')
    
    while frontier:
        # Stop early because taking too long will fail the game anyway
        if time.perf_counter() - t_start > 0.80:
            break
            
        curr_f, _, curr_node = heapq.heappop(frontier)
        rob_pos, curr_bxs = curr_node
        
        # Count how many boxes are currently sitting on goals
        curr_score = 0
        for b in curr_bxs:
            if b in targets:
                curr_score += 1
                
        if curr_score > base_score:
            # print("Found a move that places a box on a target")
            # Once a box reaches a goal, use the path that got it there
            temp = curr_node
            path = []
            while came_from[temp][0] != init_state:
                path.append(came_from[temp][1])
                temp = came_from[temp][0]
                if not temp: break
            if temp:
                path.append(came_from[temp][1])
                path.reverse()
                cached_plan = path[1:]
                last_known_boxes = boxes.copy()
                return path[0]
                
        for action, (dx, dy) in zip(['N','S','E','W'], [(0,-1),(0,1),(1,0),(-1,0)]):
            new_rx, new_ry = rob_pos[0] + dx, rob_pos[1] + dy
            
            # Do not move into a wall or the other robot
            if (new_rx, new_ry) in walls or (new_rx, new_ry) == other_pos:
                continue
                
            next_bxs = set(curr_bxs)
            if (new_rx, new_ry) in curr_bxs:
                push_x, push_y = new_rx + dx, new_ry + dy
                
                # There must be space behind the box for the push to work
                if (push_x, push_y) in walls or (push_x, push_y) in curr_bxs or (push_x, push_y) == other_pos:
                    continue
                    
                next_bxs.remove((new_rx, new_ry))
                next_bxs.add((push_x, push_y))
                
            next_st = ((new_rx, new_ry), frozenset(next_bxs))
            
            # Avoid moves that leave the box permanently stuck
            if (new_rx, new_ry) in curr_bxs:
                if check_corner_trap([(push_x, push_y)], walls, targets):
                    continue
                
            temp_g = g_score[curr_node] + 1
            
            if next_st not in g_score or temp_g < g_score[next_st]:
                g_score[next_st] = temp_g
                came_from[next_st] = (curr_node, action)
                
                # The score roughly combines box distance and robot distance
                h = 0
                for box in next_st[1]:
                    if box not in targets:
                        h += bfs_cache.get(box, 9999)
                        
                unplaced_boxes = [b for b in next_st[1] if b not in targets]
                if unplaced_boxes:
                    min_agent_dist = min(max(abs(new_rx - bx), abs(new_ry - by)) for bx, by in unplaced_boxes)
                    h += min_agent_dist
                        
                f = temp_g + h
                
                if h < best_h:
                    best_h = h
                    best_node = next_st
                    
                push_count += 1
                heapq.heappush(frontier, (f, push_count, next_st))
                
    if best_node != init_state:
        # If time runs out, use the best partial path we found
        temp = best_node
        path = []
        while came_from[temp][0] != init_state:
            path.append(came_from[temp][1])
            temp = came_from[temp][0]
            if temp is None: break
        if temp is not None:
            path.append(came_from[temp][1])
            path.reverse()
            cached_plan = path[1:]
            last_known_boxes = boxes.copy()
            return path[0]
            
    return 'STAY'
