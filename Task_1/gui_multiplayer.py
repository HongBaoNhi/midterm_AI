import pygame
import sys
import importlib
from multi_env import MultiEnv

def start_multiplayer():
    # print("Starting multiplayer GUI")
    pygame.init()
    
    win = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Sokoban AI Arena")
    
    big_font = pygame.font.SysFont(None, 40)
    med_font = pygame.font.SysFont(None, 28)
    
    level_files = ['2_box_map.txt', '4_box_map.txt', '4_box_map_2.txt']
    curr_map = 0
    
    bot_types = ['A*', 'UCS', 'BFS']
    bot1_sel = 0
    bot2_sel = 1
    
    step_limit = 100
    curr_screen = 'MENU'
    
    fps = pygame.time.Clock()
    
    while True:
        if curr_screen == 'MENU':
            while curr_screen == 'MENU':
                # Dark background for the menu
                win.fill((20, 24, 33))
                
                # Draw the main menu panel
                panel = pygame.Rect(100, 50, 600, 500)
                pygame.draw.rect(win, (35, 42, 56), panel, border_radius=15)
                pygame.draw.rect(win, (0, 200, 255), panel, width=3, border_radius=15)
                
                # Show the menu title
                txt_title = big_font.render("Sokoban AI Arena", True, (255, 255, 255))
                rect_title = txt_title.get_rect(center=(400, 90))
                win.blit(txt_title, rect_title)
                
                # Keep all buttons using the same layout
                def draw_btn(y, text, color, font, is_big=False):
                    # print("Drawing menu button:", text)
                    w, h = (450, 60) if is_big else (400, 50)
                    r = pygame.Rect(0, 0, w, h)
                    r.center = (400, y)
                    
                    # Add a small shadow behind the button
                    sh = r.copy()
                    sh.y += 4
                    pygame.draw.rect(win, (15, 20, 28), sh, border_radius=10)
                    
                    pygame.draw.rect(win, color, r, border_radius=10)
                    
                    txt = font.render(text, True, (255, 255, 255) if color != (45, 54, 72) else (220, 220, 220))
                    win.blit(txt, txt.get_rect(center=r.center))
                    
                # Place the options with even spacing
                draw_btn(160, f"Map (Press M): {level_files[curr_map]}", (45, 54, 72), med_font)
                draw_btn(240, f"Agent 1 (Press 1): {bot_types[bot1_sel]}", (0, 100, 255), med_font)
                draw_btn(320, f"Agent 2 (Press 2): {bot_types[bot2_sel]}", (255, 140, 0), med_font)
                draw_btn(400, f"Max Steps (Press UP/DOWN): {step_limit}", (45, 54, 72), med_font)
                draw_btn(490, "Press ENTER to Start!", (46, 204, 113), big_font, True)
                
                pygame.display.flip()
                
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_m:
                            curr_map = (curr_map + 1) % len(level_files)
                        elif ev.key == pygame.K_1:
                            bot1_sel = (bot1_sel + 1) % len(bot_types)
                        elif ev.key == pygame.K_2:
                            bot2_sel = (bot2_sel + 1) % len(bot_types)
                        elif ev.key == pygame.K_UP:
                            step_limit += 10
                        elif ev.key == pygame.K_DOWN:
                            step_limit = max(10, step_limit - 10)
                        elif ev.key == pygame.K_RETURN or ev.key == pygame.K_KP_ENTER:
                            curr_screen = 'PLAYING'
                        elif ev.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()
                
                fps.tick(30)
                
        elif curr_screen == 'PLAYING':
            bot_files = {
                'A*': 'agent_1',
                'UCS': 'agent_2',
                'BFS': 'agent_3'
            }

            file_bot_1 = bot_files[bot_types[bot1_sel]]
            file_bot_2 = bot_files[bot_types[bot2_sel]]

            if file_bot_1 == file_bot_2:
                file_bot_2 += "_clone"

            module1 = importlib.import_module(file_bot_1)
            module2 = importlib.import_module(file_bot_2)
            
            arena = MultiEnv(level_files[curr_map])
            
            # Set up the game window and board size
            TILE = 64
            w = max([x for x, y in arena.walls]) + 1
            h = max([y for x, y in arena.walls]) + 1
            max_travel_time = w * h
            
            win = pygame.display.set_mode((w * TILE, h * TILE))
            pygame.display.set_caption("Sokoban AI Arena - MATCH ONGOING")
            
            is_paused = False
            do_restart = False
            anim_progress = 1.0
            
            step_count = 0
            no_progress_count = 0
            visited_global_states = set()
            
            def get_current_frame():
                # print("Reading replay frame:", frame_idx)
                return {
                    'a1': arena.a1_pos, 'a2': arena.a2_pos,
                    'boxes': arena.boxes.copy(), 'owner': arena.owner.copy(),
                    's1': arena.a1_score, 's2': arena.a2_score
                }
            
            old_frame = get_current_frame()
            new_frame = get_current_frame()
            match_over = False
            
            a1_history = []
            a2_history = []
            
            while curr_screen == 'PLAYING':
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_ESCAPE:
                            curr_screen = 'MENU'
                            # Return the window to its normal size
                            win = pygame.display.set_mode((800, 600))
                        elif ev.key == pygame.K_r:
                            do_restart = True
                            break
                        elif ev.key == pygame.K_SPACE:
                            is_paused = not is_paused
                                
                if do_restart:
                    break
                    
                if curr_screen != 'PLAYING':
                    break
                    
                if not is_paused:
                    if anim_progress < 1.0:
                        anim_progress += 0.1
                    elif not match_over:
                        anim_progress = 0.0
                        old_frame = get_current_frame()
                        
                        current_hash = (arena.a1_pos, arena.a2_pos, frozenset(arena.boxes))
                        if current_hash in visited_global_states:
                            print("Cycle detected! Agents are looping. Match ended.")
                            print(f"Total cost (steps): {step_count}")
                            print(f"Agent 1 Score: {arena.a1_score} | Actions: {a1_history}")
                            print(f"Agent 2 Score: {arena.a2_score} | Actions: {a2_history}")
                            match_over = True
                        visited_global_states.add(current_hash)
                        
                        if not match_over:
                            # Process events before and after the environment step
                            pygame.event.pump()
                            old_boxes = arena.boxes.copy()
                            
                            act1, act2 = arena.step(module1, module2)
                            a1_history.append(act1)
                            a2_history.append(act2)
                            
                            pygame.event.pump()
                            
                            if arena.boxes == old_boxes:
                                no_progress_count += 1
                            else:
                                no_progress_count = 0
                                
                            step_count += 1
                            new_frame = get_current_frame()
                            
                            if arena.targets.issubset(arena.boxes):
                                print(f"\nMatch over! All targets secured at step {step_count}.")
                                print(f"Total cost (steps): {step_count}")
                                print(f"Agent 1 Score: {arena.a1_score} | Actions: {a1_history}")
                                print(f"Agent 2 Score: {arena.a2_score} | Actions: {a2_history}")
                                match_over = True
                            elif no_progress_count >= max_travel_time:
                                print(f"\nDynamic Deadlock detected! No boxes moved for {max_travel_time} steps. Match ended early.")
                                print(f"Total cost (steps): {step_count}")
                                print(f"Agent 1 Score: {arena.a1_score} | Actions: {a1_history}")
                                print(f"Agent 2 Score: {arena.a2_score} | Actions: {a2_history}")
                                match_over = True
                            elif step_count >= step_limit:
                                print("\nStep limit reached!")
                                print(f"Total cost (steps): {step_count}")
                                print(f"Agent 1 Score: {arena.a1_score} | Actions: {a1_history}")
                                print(f"Agent 2 Score: {arena.a2_score} | Actions: {a2_history}")
                                match_over = True
                        
                frame = old_frame
                next_frame = new_frame
                
                old_boxes = frame['boxes']
                new_boxes = next_frame['boxes']
                
                static_boxes = old_boxes
                moved_old_pos = set()
                moved_new_pos = set()
                
                if anim_progress > 0.0 and next_frame != frame:
                    static_boxes = old_boxes.intersection(new_boxes)
                    moved_old_pos = old_boxes - new_boxes
                    moved_new_pos = new_boxes - old_boxes
                    
                # Match boxes to targets using their distances
                moved_boxes = {}
                for m_old in moved_old_pos:
                    for m_new in moved_new_pos:
                        if abs(m_new[0] - m_old[0]) + abs(m_new[1] - m_old[1]) == 1:
                            moved_boxes[m_old] = m_new
                                        
                win.fill((20, 24, 33)) # Fill the window with the dark background
                
                for r_y in range(h):
                    for r_x in range(w):
                        draw_box = pygame.Rect(r_x * TILE, r_y * TILE, TILE, TILE)
                        
                        if (r_x, r_y) in arena.walls:
                            # Draw walls as solid blocks with a small inner border
                            pygame.draw.rect(win, (60, 70, 90), draw_box)
                            pygame.draw.rect(win, (45, 54, 72), draw_box.inflate(-4, -4))
                            
                        if (r_x, r_y) in arena.targets:
                            # Draw targets as circles with a simple marker
                            t_cx = r_x * TILE + TILE // 2
                            t_cy = r_y * TILE + TILE // 2
                            pygame.draw.circle(win, (70, 80, 100), (t_cx, t_cy), TILE // 4, width=2)
                            pygame.draw.line(win, (70, 80, 100), (t_cx - 8, t_cy), (t_cx + 8, t_cy), 2)
                            pygame.draw.line(win, (70, 80, 100), (t_cx, t_cy - 8), (t_cx, t_cy + 8), 2)
                            
                for (r_x, r_y) in static_boxes:
                    draw_box = pygame.Rect(r_x * TILE, r_y * TILE, TILE, TILE)
                    if (r_x, r_y) in arena.targets:
                        # Target boxes use the owner tag to show who placed them
                        owner_tag = frame['owner'].get((r_x, r_y), 0)
                        if owner_tag == 1:
                            box_color = (0, 120, 255)
                            inner_color = (100, 180, 255)
                        elif owner_tag == 2:
                            box_color = (255, 140, 0)
                            inner_color = (255, 180, 80)
                        else:
                            box_color = (139, 69, 19)
                            inner_color = (180, 100, 40)
                    else:
                        box_color = (139, 69, 19)
                        inner_color = (180, 100, 40)
                    pygame.draw.rect(win, box_color, draw_box.inflate(-8, -8), border_radius=8)
                    pygame.draw.rect(win, inner_color, draw_box.inflate(-16, -16), border_radius=4)
                    
                for old_b, new_b in moved_boxes.items():
                    # Interpolate between both positions so box movement looks smooth
                    cur_bx = old_b[0] + (new_b[0] - old_b[0]) * anim_progress
                    cur_by = old_b[1] + (new_b[1] - old_b[1]) * anim_progress
                    draw_box = pygame.Rect(int(cur_bx * TILE), int(cur_by * TILE), TILE, TILE)
                    
                    # Use the frame that the animation has mostly reached
                    target_b = new_b if anim_progress > 0.5 else old_b
                    if target_b in arena.targets:
                        # Prefer the new owner, but keep the old tag during the transition
                        owner_tag = next_frame['owner'].get(new_b, frame['owner'].get(old_b, 0))
                        if owner_tag == 1:
                            box_color = (0, 120, 255)
                            inner_color = (100, 180, 255)
                        elif owner_tag == 2:
                            box_color = (255, 140, 0)
                            inner_color = (255, 180, 80)
                        else:
                            box_color = (139, 69, 19)
                            inner_color = (180, 100, 40)
                    else:
                        box_color = (139, 69, 19)
                        inner_color = (180, 100, 40)
                    pygame.draw.rect(win, box_color, draw_box.inflate(-8, -8), border_radius=8)
                    pygame.draw.rect(win, inner_color, draw_box.inflate(-16, -16), border_radius=4)
                            
                # Draw both agents on the board
                ax1, ay1 = frame['a1']
                if anim_progress > 0.0 and next_frame != frame:
                    n_ax1, n_ay1 = next_frame['a1']
                    ax1 = ax1 + (n_ax1 - ax1) * anim_progress
                    ay1 = ay1 + (n_ay1 - ay1) * anim_progress
                    
                b1_cx = int(ax1 * TILE + TILE // 2)
                b1_cy = int(ay1 * TILE + TILE // 2)
                # Give each agent a glow and a small centre icon
                pygame.draw.circle(win, (100, 180, 255), (b1_cx, b1_cy), TILE // 2 - 4)
                pygame.draw.circle(win, (0, 100, 255), (b1_cx, b1_cy), TILE // 2 - 8)
                pygame.draw.circle(win, (255, 255, 255), (b1_cx, b1_cy), 4)
                
                ax2, ay2 = frame['a2']
                if anim_progress > 0.0 and next_frame != frame:
                    n_ax2, n_ay2 = next_frame['a2']
                    ax2 = ax2 + (n_ax2 - ax2) * anim_progress
                    ay2 = ay2 + (n_ay2 - ay2) * anim_progress
                    
                b2_cx = int(ax2 * TILE + TILE // 2)
                b2_cy = int(ay2 * TILE + TILE // 2)
                pygame.draw.circle(win, (255, 200, 100), (b2_cx, b2_cy), TILE // 2 - 4)
                pygame.draw.circle(win, (255, 140, 0), (b2_cx, b2_cy), TILE // 2 - 8)
                pygame.draw.circle(win, (255, 255, 255), (b2_cx, b2_cy), 4)
                
                # Put the scoreboard in a dark strip at the top
                overlay = pygame.Surface((w * TILE, 40), pygame.SRCALPHA)
                overlay.fill((20, 24, 33, 200))
                win.blit(overlay, (0, 0))
                
                txt_score = med_font.render(f"Step {step_count}/{step_limit} | A1 ({bot_types[bot1_sel]}): {frame['s1']} | A2 ({bot_types[bot2_sel]}): {frame['s2']}", True, (255, 255, 255))
                win.blit(txt_score, (10, 10))
                
                if is_paused or match_over:
                    # Make the scoreboard background slightly transparent
                    overlay_full = pygame.Surface((w * TILE, h * TILE), pygame.SRCALPHA)
                    overlay_full.fill((20, 24, 33, 180)) 
                    win.blit(overlay_full, (0, 0))
                    
                    if is_paused:
                        txt_banner = big_font.render("PAUSED", True, (255, 255, 255))
                        txt_sub = med_font.render("Space to play, ESC to Menu, R to Restart", True, (200, 200, 200))
                        border_color = (0, 200, 255)
                    else:
                        txt_banner = big_font.render("MATCH OVER", True, (255, 50, 50))
                        txt_sub = med_font.render("ESC to Menu, R to Restart", True, (200, 200, 200))
                        border_color = (255, 50, 50)
                        
                    banner_rect = txt_banner.get_rect(center=(w * TILE // 2, h * TILE // 2 - 20))
                    sub_rect = txt_sub.get_rect(center=(w * TILE // 2, h * TILE // 2 + 20))
                    
                    banner_bg = pygame.Rect(0, 0, max(banner_rect.width, sub_rect.width) + 60, 120)
                    banner_bg.center = (w * TILE // 2, h * TILE // 2)
                    pygame.draw.rect(win, (35, 42, 56), banner_bg, border_radius=15)
                    pygame.draw.rect(win, border_color, banner_bg, width=3, border_radius=15)
                    
                    win.blit(txt_banner, banner_rect)
                    win.blit(txt_sub, sub_rect)
                
                pygame.display.flip()
                fps.tick(60)

if __name__ == "__main__":
    start_multiplayer()
