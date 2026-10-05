import time
from sokoban_core import SokobanGame
from search_solver import ucs, a_star

class CountingGame(SokobanGame):
    def __init__(self, filename):
        super().__init__(filename)
        self.nodes_expanded = 0
        
    def get_successors(self, current_s):
        self.nodes_expanded += 1
        return super().get_successors(current_s)

def run_tests(map_name, name_of_algo, algo_ref):
    test_game = CountingGame(map_name)
    t0 = time.perf_counter()
    result_path = algo_ref(test_game, time_limit=5.0)
    t1 = time.perf_counter()
    run_time_ms = (t1 - t0) * 1000
    expanded = test_game.nodes_expanded
    
    if result_path is None:
        if run_time_ms >= 5000:
            return "Timeout", str(expanded), "-"
        else:
            return "No solution", str(expanded), "-"
    p_len = len(result_path)
    return f"{run_time_ms:.2f}", str(expanded), str(p_len)

if __name__ == "__main__":
    test_maps = ["mini_map.txt", "example_map.txt"]
    algorithms_to_run = [("UCS", ucs), ("A*", a_star)]
    print("-" * 65)
    print("Map                  | Algorithm  | Time (ms)  | Nodes Exp | Path Len")
    print("-" * 65)
    for m in test_maps:
        for algo_name, algo_func in algorithms_to_run:
            t_res, n_res, p_res = run_tests(m, algo_name, algo_func)
            print(f"{m:20} | {algo_name:10} | {t_res:10} | {n_res:9} | {p_res}")
    print("-" * 65)