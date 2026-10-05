import time
from sokoban_core import SokobanGame
from search_solver import ucs, a_star

# I made a small subclass so we can count successor calls during the test
class CountingGame(SokobanGame):
    def __init__(self, filename):
        # print("Starting counted game for:", filename)
        super().__init__(filename)
        self.nodes_expanded = 0

    def get_successors(self, current_s):
        # print("Successor call number:", self.node_count + 1)
        self.nodes_expanded += 1
        # Keep the normal successor behaviour and only add the counter
        return super().get_successors(current_s)

def run_tests(map_name, name_of_algo, algo_ref):
    # print("Testing", name_of_algo, "on", map_name)
    # Create the test game
    test_game = CountingGame(map_name)
    
    t0 = time.perf_counter()
    # Give the solver a few seconds before stopping it
    result_path = algo_ref(test_game, time_limit=5.0)
    t1 = time.perf_counter()
    
    run_time_ms = (t1 - t0) * 1000
    
    expanded = test_game.nodes_expanded
    
    # Keep failed runs from stopping the whole experiment
    if result_path is None:
        if run_time_ms >= 5000:
            return "Timeout", str(expanded), "-"
        else:
            return "No solution", str(expanded), "-"
            
    p_len = 0
    for step in result_path:
        p_len += 1
    
    return f"{run_time_ms:.2f}", str(expanded), str(p_len)

if __name__ == "__main__":
    test_maps = ["mini_map.txt", "example_map.txt"]
    algorithms_to_run = [("UCS", ucs), ("A*", a_star)]
    
    print("-" * 65)
    print("Map                  | Algorithm  | Time (ms)  | Nodes Exp | Path Len")
    print("-" * 65)
    
    for mf in test_maps:
        for a_name, a_func in algorithms_to_run:
            time_val, nodes_val, path_val = run_tests(mf, a_name, a_func)
            
            # Make the result easier to read in the terminal
            print(f"{mf:<20} | {a_name:<10} | {time_val:<10} | {nodes_val:<9} | {path_val:<8}")
            
    print("-" * 65)
