import time
import heapq
from sokoban_core import SokobanState, SokobanGame

def check_if_stuck(box_coord, game_env):
    # print("Checking box for deadlock:", box_coord)
    if box_coord in game_env.targets:
        return False
        
    b_x, b_y = box_coord
    
    wall_top = (b_x, b_y - 1) in game_env.walls
    wall_bottom = (b_x, b_y + 1) in game_env.walls
    wall_left = (b_x - 1, b_y) in game_env.walls
    wall_right = (b_x + 1, b_y) in game_env.walls
    
    # 1. Corner deadlock
    # A box in a two-wall corner cannot be pulled back out
    if (wall_top or wall_bottom) and (wall_left or wall_right):
        return True
        
    # 2. Horizontal edge deadlock
    # Check whether the box has any useful exit along this wall
    if wall_top or wall_bottom:
        step_y = -1 if wall_top else 1
        
        curr_x = b_x
        corner_on_left = False
        
        while True:
            if (curr_x, b_y) in game_env.walls:
                break
                
            if (curr_x, b_y) in game_env.targets:
                break
                
            if (curr_x, b_y + step_y) not in game_env.walls:
                break
                
            if (curr_x - 1, b_y) in game_env.walls:
                corner_on_left = True
                break
                
            curr_x = curr_x - 1
            
        curr_x = b_x
        corner_on_right = False
        while True:
            if (curr_x, b_y) in game_env.walls:
                break
            if (curr_x, b_y) in game_env.targets:
                break
            if (curr_x, b_y + step_y) not in game_env.walls:
                break
            if (curr_x + 1, b_y) in game_env.walls:
                corner_on_right = True
                break
            curr_x = curr_x + 1
            
        if corner_on_left and corner_on_right:
            return True
            
    # Vertical edge deadlock
    if wall_left or wall_right:
        step_x = -1 if wall_left else 1
        
        curr_y = b_y
        corner_on_top = False
        while True:
            if (b_x, curr_y) in game_env.walls:
                break
            if (b_x, curr_y) in game_env.targets:
                break
            if (b_x + step_x, curr_y) not in game_env.walls:
                break
            if (b_x, curr_y - 1) in game_env.walls:
                corner_on_top = True
                break
            curr_y = curr_y - 1
            
        curr_y = b_y
        corner_on_bottom = False
        while True:
            if (b_x, curr_y) in game_env.walls:
                break
            if (b_x, curr_y) in game_env.targets:
                break
            if (b_x + step_x, curr_y) not in game_env.walls:
                break
            if (b_x, curr_y + 1) in game_env.walls:
                corner_on_bottom = True
                break
            curr_y = curr_y + 1
            
        if corner_on_top and corner_on_bottom:
            return True
            
    return False

def calculate_heuristic(current_state, game_instance, parent_state=None):
    # print("Calculating heuristic for:", current_state.agent_pos)
    # Reject layouts where a newly moved box is already stuck
    boxes_to_check = current_state.boxes
    if parent_state is not None:
        boxes_to_check = current_state.boxes - parent_state.boxes
        
    for b in boxes_to_check:
        if check_if_stuck(b, game_instance):
            return 999999
            
    # BFS precomputation: calculate these distances once and reuse them
    if not hasattr(game_instance, 'precomputed_bfs'):
        game_instance.precomputed_bfs = {}
        for t_x, t_y in game_instance.targets:
            game_instance.precomputed_bfs[(t_x, t_y)] = {}
            
            bfs_queue = [(t_x, t_y, 0)]
            visited_nodes = set()
            visited_nodes.add((t_x, t_y))
            
            while len(bfs_queue) > 0:
                cur_x, cur_y, dist = bfs_queue.pop(0)
                
                game_instance.precomputed_bfs[(t_x, t_y)][(cur_x, cur_y)] = dist
                
                for move_x, move_y in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
                    next_x = cur_x + move_x
                    next_y = cur_y + move_y
                    
                    if (next_x, next_y) not in game_instance.walls:
                        if (next_x, next_y) not in visited_nodes:
                            visited_nodes.add((next_x, next_y))
                            bfs_queue.append((next_x, next_y, dist + 1))
                        
    heuristic_score = 0
    
    for b_pos in current_state.boxes:
        # Use the closest reachable target as this box's estimated cost
        smallest_dist = 99999
        for t_pos in game_instance.targets:
            dist_val = game_instance.precomputed_bfs[t_pos].get(b_pos, 99999)
            if dist_val < smallest_dist:
                smallest_dist = dist_val
        heuristic_score += smallest_dist
        
    if len(current_state.boxes) > 0:
        agent_x, agent_y = current_state.agent_pos
        closest_box_dist = 99999
        
        # Finished boxes do not need more agent movement
        target_boxes = set(b for b in current_state.boxes if b not in game_instance.targets)
        if target_boxes:
            q = [(agent_x, agent_y, 0)]
            visited = {(agent_x, agent_y)}
            found = False
            
            while q:
                cx, cy, dist = q.pop(0)
                # Stop at the first unfinished box reached by BFS
                if (cx, cy) in target_boxes:
                    closest_box_dist = dist
                    found = True
                    break
                    
                for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
                    nx, ny = cx + dx, cy + dy
                    if (nx, ny) not in game_instance.walls and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        q.append((nx, ny, dist + 1))
                        
            if found:
                heuristic_score += closest_box_dist
            else:
                heuristic_score += 99999
                
    return heuristic_score

def get_path(parent_tracker, end_state):
    # print("Rebuilding path from:", end_state)
    # Trace the parents backwards, then reverse the result at the end
    final_moves = []
    pointer = end_state
    
    while pointer in parent_tracker:
        prev_state, move_made = parent_tracker[pointer]
        if move_made is not None:
            final_moves.append(move_made)
        pointer = prev_state
        if pointer is None:
            break
            
    final_moves.reverse()
    return final_moves

def ucs(game_instance, time_limit=5.0):
    # print("Starting UCS with limit:", time_limit)
    t_start = time.perf_counter()
    init_state = game_instance.get_initial_state()
    
    if game_instance.is_goal(init_state):
        return []
        
    q_nodes = []
    tie_breaker = 0
    heapq.heappush(q_nodes, (0, tie_breaker, init_state))
    
    parent_tracker = {}
    parent_tracker[init_state] = (None, None)
    
    cost_so_far = {init_state: 0}
    
    while len(q_nodes) > 0:
        # Return cleanly if the search uses up its time
        if time.perf_counter() - t_start > time_limit:
            return None
            
        cur_cost, _, cur_state = heapq.heappop(q_nodes)
        
        if game_instance.is_goal(cur_state):
            # print("UCS found a solution with cost:", cur_cost)
            return get_path(parent_tracker, cur_state)
            
        for child_state, move in game_instance.get_successors(cur_state):
            temp_cost = cost_so_far[cur_state] + 1
            
            if child_state not in cost_so_far or temp_cost < cost_so_far[child_state]:
                cost_so_far[child_state] = temp_cost
                parent_tracker[child_state] = (cur_state, move)
                
                tie_breaker += 1
                heapq.heappush(q_nodes, (temp_cost, tie_breaker, child_state))
                
    return None

def a_star(game_instance, time_limit=5.0):
    # print("Starting A* with limit:", time_limit)
    t_start = time.perf_counter()
    init_state = game_instance.get_initial_state()
    
    if game_instance.is_goal(init_state):
        return []
        
    priority_q = []
    seq_num = 0
    
    start_h = calculate_heuristic(init_state, game_instance)
    start_f = 0 + start_h
    
    heapq.heappush(priority_q, (start_f, seq_num, init_state))
    
    parent_map = {}
    parent_map[init_state] = (None, None)
    
    g_costs = {init_state: 0}
    
    while len(priority_q) > 0:
        # Keep the timeout check inside the search loop
        if time.perf_counter() - t_start > time_limit:
            return None
            
        cur_f, _, cur_st = heapq.heappop(priority_q)
        
        if game_instance.is_goal(cur_st):
            # print("A* found a solution with cost:", cur_f)
            return get_path(parent_map, cur_st)
            
        for n_state, act in game_instance.get_successors(cur_st):
            temp_g = g_costs[cur_st] + 1
            
            if n_state not in g_costs or temp_g < g_costs[n_state]:
                g_costs[n_state] = temp_g
                parent_map[n_state] = (cur_st, act)
                
                h_val = calculate_heuristic(n_state, game_instance, cur_st)
                
                if h_val >= 999999:
                    continue
                    
                next_f = temp_g + h_val
                seq_num += 1
                heapq.heappush(priority_q, (next_f, seq_num, n_state))
                
    return None
