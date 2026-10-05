class SokobanState:
    def __init__(self, agent_pos, boxes):
        # print("Creating state:", agent_pos, boxes)
        self.agent_pos = agent_pos
        # Frozenset lets the box layout work as a dictionary key
        self.boxes = frozenset(boxes)
        
    def __eq__(self, other_obj):
        # print("Comparing states")
        # Only compare this object with another game state
        if not isinstance(other_obj, SokobanState):
            return False
            
        # Two states match when the agent and boxes share positions
        if self.agent_pos == other_obj.agent_pos:
            if self.boxes == other_obj.boxes:
                return True
        return False
        
    def __hash__(self):
        # print("Hashing state:", self.agent_pos, self.boxes)
        # Combine both parts into one hash
        return hash((self.agent_pos, self.boxes))

class SokobanGame:
    def __init__(self, map_file_path):
        # print("Loading map:", map_file_path)
        # Prepare the containers for the level data
        self.walls = set()
        self.targets = set()
        self.init_boxes = set()
        self.init_agent = None
        
        # Read the level layout from the text file
        try:
            with open(map_file_path, 'r') as file_obj:
                grid_lines = file_obj.readlines()
        except:
            print("Could not open the map file.")
            return
            
        # This scans every tile, but it only happens when loading a level
        row_idx = 0
        for line_data in grid_lines:
            clean_line = line_data.strip('\n') # Keep spaces because they describe the map
            
            col_idx = 0
            for character in clean_line:
                if character == '%':
                    self.walls.add((col_idx, row_idx))
                elif character == 'A':
                    self.init_agent = (col_idx, row_idx)
                elif character == 'B':
                    self.init_boxes.add((col_idx, row_idx))
                elif character == 'D':
                    self.targets.add((col_idx, row_idx))
                elif character == 'C':
                    # This tile contains both a box and a target
                    self.init_boxes.add((col_idx, row_idx))
                    self.targets.add((col_idx, row_idx))
                    
                col_idx += 1
            row_idx += 1
            
        # print("Agent spawned at", self.init_agent)
        
    def get_initial_state(self):
        # print("Returning initial state:", self.init_agent, self.init_boxes)
        # Start the search from the initial state
        return SokobanState(self.init_agent, self.init_boxes)
        
    def get_successors(self, current_st):
        # print("Generating successors for:", current_st.agent_pos)
        kids = []
        
        # Try the four possible movement directions
        move_list = [
            ('N', (0, -1)),
            ('S', (0, 1)),
            ('E', (1, 0)),
            ('W', (-1, 0))
        ]
        
        a_x = current_st.agent_pos[0]
        a_y = current_st.agent_pos[1]
        
        for move_name, delta in move_list:
            next_ax = a_x + delta[0]
            next_ay = a_y + delta[1]
            proposed_pos = (next_ax, next_ay)
            
            # Walls cannot be entered
            if proposed_pos in self.walls:
                continue # Ignore this direction
                
            # Check whether this move pushes a box
            if proposed_pos in current_st.boxes:
                # Find the tile where the box would land
                b_next_x = next_ax + delta[0]
                b_next_y = next_ay + delta[1]
                pushed_box_pos = (b_next_x, b_next_y)
                
                # A push fails if the landing tile is occupied
                if pushed_box_pos in self.walls:
                    continue
                if pushed_box_pos in current_st.boxes:
                    continue
                    
                # Replace the old box position with the new one
                new_box_set = set()
                for box in current_st.boxes:
                    new_box_set.add(box)
                    
                new_box_set.remove(proposed_pos)
                new_box_set.add(pushed_box_pos)
                
                new_state = SokobanState(proposed_pos, new_box_set)
                kids.append((new_state, move_name))
                
            else:
                # This move only changes the agent position
                new_state = SokobanState(proposed_pos, current_st.boxes)
                kids.append((new_state, move_name))
                
        # print("Found", len(kids), "children")
        return kids
        
    def is_goal(self, st):
        # print("Checking goal state:", st.boxes)
        # Every box must be on a target for the level to be complete
        for box in st.boxes:
            if box not in self.targets:
                return False
        return True
