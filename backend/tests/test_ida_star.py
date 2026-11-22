import sys
import time
from pathlib import Path

# Ensure backend root is in sys.path for direct execution
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.cube.moves import apply_moves
from app.cube.scramble import generate_scramble
from app.cube.serialization import faces_from_state
from app.cube.state import CubeState
from app.solver.solver import get_algorithms


def format_cube_faces(faces: dict[str, list[str]]) -> str:
    """Pretty-print 6-face sticker dictionary."""
    lines = []
    # Face net layout:
    #      [U]
    # [L]  [F]  [R]  [B]
    #      [D]
    u = faces["U"]
    d = faces["D"]
    l = faces["L"]
    f = faces["F"]
    r = faces["R"]
    b = faces["B"]

    lines.append(f"       +-----+")
    lines.append(f"       | {u[0]} {u[1]} |  (Up)")
    lines.append(f"       | {u[2]} {u[3]} |")
    lines.append(f" +-----+-----+-----+-----+")
    lines.append(f" | {l[0]} {l[1]} | {f[0]} {f[1]} | {r[0]} {r[1]} | {b[0]} {b[1]} |  (Left, Front, Right, Back)")
    lines.append(f" | {l[2]} {l[3]} | {f[2]} {f[3]} | {r[2]} {r[3]} | {b[2]} {b[3]} |")
    lines.append(f" +-----+-----+-----+-----+")
    lines.append(f"       | {d[0]} {d[1]} |  (Down)")
    lines.append(f"       | {d[2]} {d[3]} |")
    lines.append(f"       +-----+")
    return "\n".join(lines)


def run_ida_star_test(scramble_length: int | None = None, label: str = "Random Scramble"):
    """
    Generate a scramble, solve it using IDA*, and print full state & path diagnostics.
    """
    algorithms = get_algorithms()

    print("\n" + "=" * 70)
    print(f"  IDA* ALGORITHM TEST: {label.upper()}")
    print("=" * 70)

    # 1. Scramble Generation
    start_scramble_time = time.perf_counter()
    scrambled_state, scramble_moves = generate_scramble(length=scramble_length)
    scramble_duration = (time.perf_counter() - start_scramble_time) * 1000

    print("\n[1] SCRAMBLE GENERATION:")
    print(f"  * Move Count  : {len(scramble_moves)}")
    print(f"  * Moves       : {' '.join(scramble_moves)}")
    print(f"  * Scramble Time : {scramble_duration:.3f} ms")

    # 2. Details of Initial (Scrambled) State
    initial_faces = faces_from_state(scrambled_state)
    h_pdb1 = algorithms.pdb1.heuristic(scrambled_state)
    h_pdb2 = algorithms.pdb2.heuristic(scrambled_state)
    h_initial = max(h_pdb1, h_pdb2)

    print("\n[2] INITIAL (SCRAMBLED) CUBE STATE:")
    print(f"  * Corner Permutation (cp) : {scrambled_state.cp}")
    print(f"  * Corner Orientation (co) : {scrambled_state.co}")
    print(f"  * PDB1 Heuristic (corners 0-3): {h_pdb1}")
    print(f"  * PDB2 Heuristic (corners 4-7): {h_pdb2}")
    print(f"  * Combined Admissible h(s)    : {h_initial}")
    print(f"  * State Validity             : {scrambled_state.is_valid()}")
    print(f"  * Is Solved                  : {scrambled_state.is_solved()}")
    print("\n  Facelet Net Layout:")
    print(format_cube_faces(initial_faces))

    # 3. Solve using IDA*
    print("\n[3] RUNNING IDA* SEARCH...")
    start_solve_time = time.perf_counter()
    solution = algorithms.IDA_star(scrambled_state)
    solve_duration = (time.perf_counter() - start_solve_time) * 1000

    assert solution is not None, "IDA* failed to find a solution!"

    # 4. Solution Details
    print("\n[4] SOLUTION RESULTS:")
    print(f"  * Solution Found     : {' '.join(solution) if solution else '(already solved)'}")
    print(f"  * Solution Step Count: {len(solution)} moves")
    print(f"  * Search Duration    : {solve_duration:.2f} ms ({solve_duration / 1000:.4f} s)")

    # 5. Apply Solution and Verify Final State
    final_state = apply_moves(scrambled_state, solution)
    final_faces = faces_from_state(final_state)

    print("\n[5] FINAL (SOLVED) CUBE STATE:")
    print(f"  * Corner Permutation (cp) : {final_state.cp}")
    print(f"  * Corner Orientation (co) : {final_state.co}")
    print(f"  * State Validity             : {final_state.is_valid()}")
    print(f"  * Is Solved                  : {final_state.is_solved()}")
    print("\n  Facelet Net Layout:")
    print(format_cube_faces(final_faces))

    # Assertions
    assert final_state.is_solved(), "Cube state is not solved after applying IDA* solution!"
    assert final_state == CubeState.solved()
    print("\n" + "=" * 70)
    print(f"  SUCCESS: Cube verified solved in {len(solution)} moves.")
    print("=" * 70 + "\n")

    return {
        "scramble_moves": scramble_moves,
        "solution_moves": solution,
        "solve_duration_ms": solve_duration,
        "is_solved": final_state.is_solved(),
    }


def test_ida_star_random_scramble():
    """Test IDA* with a default random scramble and print all details."""
    result = run_ida_star_test(scramble_length=None, label="Default Random Scramble")
    assert result["is_solved"]


def test_ida_star_worst_case_scramble():
    """Test IDA* on a worst-case scenario scramble (11 moves) and print all details."""
    result = run_ida_star_test(scramble_length=11, label="Worst-Case Scenario (11 Moves)")
    assert result["is_solved"]


if __name__ == "__main__":
    # Allows running directly: python tests/test_ida_star.py
    run_ida_star_test(scramble_length=None, label="Default Scramble")
    run_ida_star_test(scramble_length=11, label="Worst-Case Scramble")
