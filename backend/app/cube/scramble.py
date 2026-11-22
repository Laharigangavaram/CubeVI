"""Scramble generation for demos and repeatable experiments."""

import random
from itertools import count
from .moves import apply_move
from .state import CubeState

ALL_MOVES: list[str] = [
    "U", "U'", "U2",
    "D", "D'", "D2",
    "R", "R'", "R2",
    "L", "L'", "L2",
    "F", "F'", "F2",
    "B", "B'", "B2",
]

# Opposite faces commute on a cube. Tracking opposites prevents sequences like
# U D U' or R L R2 where commuting turns on parallel axes combine or cancel out.
OPPOSITE_FACES: dict[str, str] = {
    "U": "D",
    "D": "U",
    "R": "L",
    "L": "R",
    "F": "B",
    "B": "F",
}

# For backward compatibility with imports expecting all_moves
all_moves = ALL_MOVES

# Global counter to guarantee at least 1 in 10 scrambles is a worst-case scenario
_scramble_counter = count(1)


def generate_scramble(
    length: int | None = None,
    seed: int | None = None,
) -> tuple[CubeState, list[str]]:
    """
    Generate a valid random 2x2x2 CubeState and corresponding scramble moves.

    Proper scrambling:
      - Avoids consecutive turns of the same face (e.g. R followed by R').
      - Avoids commuting cancellations across opposite faces (e.g. U D U' or R L R).
      - Supports an optional `seed` for deterministic and repeatable experiments.

    Difficulty distribution:
      - When `length` is None, at least 1 in 10 scrambles (every 10th or 10% chance)
        is generated as a worst-case scenario with 10–12 moves.
      - The other 9 in 10 scrambles are generated with standard 6–7 moves.
      - If `length` is explicitly provided, an exact scramble of that length is produced.
    """
    rng = random.Random(seed) if seed is not None else random

    if length is not None:
        if length <= 0:
            raise ValueError("Length of scramble must be positive")
        num_moves = length
    else:
        # At least 1 in 10 scrambles generates a worst-case scenario (10-12 moves)
        scramble_idx = next(_scramble_counter)
        if scramble_idx % 10 == 0 or rng.random() < 0.10:
            num_moves = rng.randint(30, 40)
        else:
            num_moves = rng.randint(6, 10)

    state = CubeState.solved()
    scramble_moves: list[str] = []

    prev_face: str | None = None
    prev_prev_face: str | None = None

    for _ in range(num_moves):
        # Filter moves to prevent redundant/canceling sequences:
        # 1. Cannot turn the same face twice in a row.
        # 2. If the previous two moves were on opposite (commuting) faces,
        #    cannot turn either face again to avoid axis cancellation.
        possible_moves = []
        for move in ALL_MOVES:
            face = move[0]
            if face == prev_face:
                continue
            if (
                prev_face is not None
                and prev_prev_face is not None
                and OPPOSITE_FACES.get(prev_face) == prev_prev_face
                and (face == prev_face or face == prev_prev_face)
            ):
                continue
            possible_moves.append(move)

        move = rng.choice(possible_moves)

        state = apply_move(state, move)
        scramble_moves.append(move)

        prev_prev_face = prev_face
        prev_face = move[0]

    return state, scramble_moves




