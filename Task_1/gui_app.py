import pygame
import sys
from sokoban_core import SokobanGame
from search_solver import a_star, ucs

def start_gui():
    # print("Starting single-player GUI")
    print("--- Sokoban Pathfinding Visualizer ---")
    map_choice = input("Enter map name (e.g. example_map.txt). Just press Enter for default: ")
    if map_choice.strip() == "":
        map_choice = 'example_map.txt'
        
    print("Algorithms:")
    print("1) UCS")
    print("2) A* (Faster)")
    user_algo = input("Pick an algorithm: ")
    
    # Load the level and prepare the game state
    game_env = SokobanGame(map_choice)
    print("Running solver... hope it doesn't freeze...")
    
    if user_algo == '1':
        solution = ucs(game_env)
    else:
        solution = a_star(game_env)
        
    if not solution:
        # print("Solver did not return a solution")
        print("Couldn't find a path! Maybe the map is impossible or it timed out.")
        sys.exit(0)
    else:
        # print("Solution loaded with", len(solution), "moves")
        # A shorter move list means a cheaper solution
        print("Found a solution! Total cost is:", len(solution))
        print("Actions:", solution)
        
    pygame.init()
        
    # Save every state so the replay slider can move backwards too
    history_states = [game_env.get_initial_state()]
    current_ptr = history_states[0]
    
    for move in solution:
        kids = game_env.get_successors(current_ptr)
        for next_st, act_made in kids:
            if act_made == move:
                history_states.append(next_st)
                current_ptr = next_st
                break
                
    CELL = 64
    # Size the window based on the level dimensions
    max_w = max([w[0] for w in game_env.walls]) + 1
    max_h = max([w[1] for w in game_env.walls]) + 1
    
    win = pygame.display.set_mode((max_w * CELL, max_h * CELL))
    pygame.display.set_caption("Sokoban AI Viewer")
    
    text_font = pygame.font.SysFont(None, 32)
    small_text = pygame.font.SysFont(None, 24)
    fps_clock = pygame.time.Clock()
    
    frame_idx = 0
    final_frame = len(history_states) - 1
    
    auto_play = False
    anim_progress = 0.0
    
    is_running = True
    while is_running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                is_running = False
                
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    is_running = False
                elif ev.key == pygame.K_SPACE:
                    auto_play = not auto_play
                elif ev.key == pygame.K_RIGHT:
                    if frame_idx < final_frame:
                        frame_idx += 1
                        anim_progress = 0.0
                elif ev.key == pygame.K_LEFT:
                    if frame_idx > 0:
                        frame_idx -= 1
                        anim_progress = 0.0
                        
        if auto_play:
            if frame_idx < final_frame:
                anim_progress += 0.1
                if anim_progress >= 1.0:
                    anim_progress = 0.0
                    frame_idx += 1
            else:
                auto_play = False
                anim_progress = 0.0
                    
        # Use a dark background for the board
        win.fill((30, 30, 30))
        
        display_state = history_states[frame_idx]
        next_state = history_states[frame_idx + 1] if frame_idx < final_frame else display_state
        
        # Compare two frames so only boxes that actually moved get animated
        old_boxes = display_state.boxes
        new_boxes = next_state.boxes
        
        static_boxes = old_boxes
        moved_old_pos = set()
        moved_new_pos = set()
        
        if anim_progress > 0.0 and next_state != display_state:
            # Boxes in both sets stay still while the changed ones are interpolated
            static_boxes = old_boxes.intersection(new_boxes)
            moved_old_pos = old_boxes - new_boxes
            moved_new_pos = new_boxes - old_boxes
            
        for y in range(max_h):
            for x in range(max_w):
                draw_rect = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
                
                if (x, y) in game_env.walls:
                    pygame.draw.rect(win, (128, 128, 128), draw_rect)
                    in_rect = draw_rect.inflate(-8, -8)
                    pygame.draw.rect(win, (80, 80, 80), in_rect)
                    
                if (x, y) in game_env.targets:
                    c_x = x * CELL + CELL // 2
                    c_y = y * CELL + CELL // 2
                    pygame.draw.circle(win, (50, 50, 50), (c_x, c_y), CELL // 4)
                    pygame.draw.line(win, (200, 0, 0), (c_x - 10, c_y - 10), (c_x + 10, c_y + 10), 3)
                    pygame.draw.line(win, (200, 0, 0), (c_x + 10, c_y - 10), (c_x - 10, c_y + 10), 3)
                    
        for bx, by in static_boxes:
            draw_rect = pygame.Rect(bx * CELL, by * CELL, CELL, CELL)
            pygame.draw.rect(win, (139, 69, 19), draw_rect)
            in_rect2 = draw_rect.inflate(-16, -16)
            if (bx, by) in game_env.targets:
                pygame.draw.rect(win, (0, 200, 0), in_rect2)
            else:
                pygame.draw.rect(win, (210, 180, 140), in_rect2)
                
        # Smoothly move sprites towards their next tile
        if moved_old_pos and moved_new_pos:
            # Pair the old and new positions to draw the box between both frames
            for m_old, m_new in zip(moved_old_pos, moved_new_pos):
                cur_bx = m_old[0] + (m_new[0] - m_old[0]) * anim_progress
                cur_by = m_old[1] + (m_new[1] - m_old[1]) * anim_progress
                draw_rect = pygame.Rect(int(cur_bx * CELL), int(cur_by * CELL), CELL, CELL)
                pygame.draw.rect(win, (139, 69, 19), draw_rect)
                in_rect2 = draw_rect.inflate(-16, -16)
                # Switch target colouring halfway through the movement
                if m_new in game_env.targets and anim_progress > 0.5 or m_old in game_env.targets and anim_progress <= 0.5:
                    pygame.draw.rect(win, (0, 200, 0), in_rect2)
                else:
                    pygame.draw.rect(win, (210, 180, 140), in_rect2)
                
        ax, ay = display_state.agent_pos
        if anim_progress > 0.0 and next_state != display_state:
            n_ax, n_ay = next_state.agent_pos
            ax = ax + (n_ax - ax) * anim_progress
            ay = ay + (n_ay - ay) * anim_progress
            
        c_x = int(ax * CELL + CELL // 2)
        c_y = int(ay * CELL + CELL // 2)
        pygame.draw.circle(win, (0, 100, 255), (c_x, c_y), CELL // 2 - 4)
        pygame.draw.circle(win, (0, 255, 255), (c_x, c_y), CELL // 2 - 4, 3)
                    
        # Draw the status information over the board
        bg_panel = pygame.Surface((500, 120))
        bg_panel.set_alpha(150)
        bg_panel.fill((0, 0, 0))
        win.blit(bg_panel, (10, 10))
        
        lbl_step = text_font.render(f"Move: {frame_idx} / {final_frame}", True, (255, 255, 255))
        win.blit(lbl_step, (20, 20))
        
        if auto_play:
            lbl_mode = text_font.render("[PLAYING]", True, (0, 255, 0))
        else:
            lbl_mode = text_font.render("[PAUSED]", True, (255, 255, 0))
        win.blit(lbl_mode, (20, 50))
        
        lbl_hint = small_text.render("SPACE = Play/Pause | ARROWS = scrub | ESC = Exit", True, (200, 200, 200))
        win.blit(lbl_hint, (20, 85))
        
        pygame.display.flip()
        fps_clock.tick(60)
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    start_gui()
