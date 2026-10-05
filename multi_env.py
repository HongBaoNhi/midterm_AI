import os

class MultiEnv:
    def __init__(self, level_file):
        # print("Loading multiplayer level:", level_file)
        # Store the board objects used by both agents
        self.walls = set()
        self.targets = set()
        self.boxes = set()
        
        self.a1_pos = None
        self.a2_pos = None
        
        self.a1_score = 0
        self.a2_score = 0
        
        # Remember which agent moved each box most recently
        self.owner = {}
        
        try:
            with open(level_file, 'r') as map_f:
                lines_data = map_f.readlines()
        except FileNotFoundError:
            print("Map file not found!")
            return
            
        row_id = 0
        for l in lines_data:
            clean_l = l.strip('\n')
            
            col_id = 0
            for char in clean_l:
                if char == '%':
                    self.walls.add((col_id, row_id))
                elif char == '1':
                    self.a1_pos = (col_id, row_id)
                elif char == '2':
                    self.a2_pos = (col_id, row_id)
                elif char == 'B':
                    self.boxes.add((col_id, row_id))
                elif char == 'D':
                    self.targets.add((col_id, row_id))
                col_id += 1
            row_id += 1
                
    def step(self, bot1, bot2):
        # print("Starting step:", self.a1_pos, self.a2_pos, self.boxes)
        # Phase 1: Ask both agents what they want to do
        # They both use the same board state before anything moves
        action1 = bot1.get_action(self.a1_pos, self.a2_pos, self.boxes, self.targets, self.walls)
        action2 = bot2.get_action(self.a2_pos, self.a1_pos, self.boxes, self.targets, self.walls)
        # print("Chosen actions:", action1, action2)
        
        move_dict = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'W': (-1, 0)}
        
        # Invalid actions are treated as staying still
        d1 = move_dict.get(action1, (0, 0))
        d2 = move_dict.get(action2, (0, 0))
        
        # Phase 2: Work out where they are trying to go
        # Turn each action into its next tile
        n1 = (self.a1_pos[0] + d1[0], self.a1_pos[1] + d1[1])
        n2 = (self.a2_pos[0] + d2[0], self.a2_pos[1] + d2[1])
        
        # Work out Agent 1's next tile
        next_pos1 = n1
        did_push1 = False
        new_b1_pos = None
        
        if next_pos1 in self.walls or next_pos1 == n2:
            next_pos1 = self.a1_pos # The move is blocked
        elif next_pos1 in self.boxes:
            # The agent is trying to push a box
            new_b1_pos = (next_pos1[0] + d1[0], next_pos1[1] + d1[1])
            if new_b1_pos in self.walls or new_b1_pos in self.boxes or new_b1_pos == n2:
                next_pos1 = self.a1_pos # The push is blocked
            else:
                did_push1 = True
                
        # Work out Agent 2's next tile
        next_pos2 = n2
        did_push2 = False
        new_b2_pos = None
        
        if next_pos2 in self.walls or next_pos2 == n1:
            next_pos2 = self.a2_pos
        elif next_pos2 in self.boxes:
            new_b2_pos = (next_pos2[0] + d2[0], next_pos2[1] + d2[1])
            if new_b2_pos in self.walls or new_b2_pos in self.boxes or new_b2_pos == n1:
                next_pos2 = self.a2_pos
            else:
                did_push2 = True
                
        # Phase 3: Sort out any clashes
        # Cancel moves if both agents try to use the same tile
        if next_pos1 == next_pos2:
            # print("Agents tried to use the same tile:", next_pos1)
            if next_pos1 != self.a1_pos or next_pos2 != self.a2_pos:
                # They both moved, so cancel both actions
                next_pos1 = self.a1_pos
                did_push1 = False
                next_pos2 = self.a2_pos
                did_push2 = False
                
        # Prevent both agents from moving boxes into the same tile
        if did_push1 and did_push2 and new_b1_pos == new_b2_pos:
            # print("Both agents tried to push into:", new_b1_pos)
            next_pos1 = self.a1_pos
            did_push1 = False
            next_pos2 = self.a2_pos
            did_push2 = False
            
        # Phase 4: Apply the moves
        # Only update the board after the conflicts are handled
        if did_push1:
            self.boxes.remove(next_pos1)
            self.boxes.add(new_b1_pos)
            
            # Update the score when a box reaches a target
            if new_b1_pos in self.targets:
                if next_pos1 not in self.targets:
                    self.a1_score += 1
                else:
                    self.a1_score += 1
                    if self.owner.get(next_pos1) == 1: self.a1_score -= 1
                    elif self.owner.get(next_pos1) == 2: self.a2_score -= 1
            elif next_pos1 in self.targets:
                if self.owner.get(next_pos1) == 1: self.a1_score -= 1
                elif self.owner.get(next_pos1) == 2: self.a2_score -= 1
                
            # Record who last pushed this box
            if next_pos1 in self.owner:
                del self.owner[next_pos1]
            self.owner[new_b1_pos] = 1
            
        if did_push2:
            # Do not let Agent 1 push the same box twice in one step
            if next_pos2 in self.boxes: 
                self.boxes.remove(next_pos2)
                self.boxes.add(new_b2_pos)
                
                if new_b2_pos in self.targets:
                    if next_pos2 not in self.targets:
                        self.a2_score += 1
                    else:
                        self.a2_score += 1
                        if self.owner.get(next_pos2) == 1: self.a1_score -= 1
                        elif self.owner.get(next_pos2) == 2: self.a2_score -= 1
                elif next_pos2 in self.targets:
                    if self.owner.get(next_pos2) == 1: self.a1_score -= 1
                    elif self.owner.get(next_pos2) == 2: self.a2_score -= 1
                        
                if next_pos2 in self.owner:
                    del self.owner[next_pos2]
                self.owner[new_b2_pos] = 2
                
        self.a1_pos = next_pos1
        self.a2_pos = next_pos2
        
        return action1, action2

if __name__ == "__main__":
    # Use gui_multiplayer.py to run this with the interface
    pass
