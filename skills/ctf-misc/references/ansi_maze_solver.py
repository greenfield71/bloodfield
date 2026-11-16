#!/usr/bin/env python3
"""ANSI terminal maze parser & BFS shortest-path solver for CTF automation.

Handles interactive challenges (e.g. L3akCTF Maze Captcha / Cursed Maze Captcha)
where the server renders an ANSI/Unicode maze under tight timeout:
1. Strip ANSI escape codes or parse colored cells into tile types
2. Parse start, goal, and traversable cells
3. Find shortest path via BFS / Dijkstra
4. Output move sequence ('wasd' or 'UDLR') for pipelined batch sending

Usage:
    python3 -I ansi_maze_solver.py solve maze.txt
    python3 -I ansi_maze_solver.py --test
"""
import collections
import re
import sys

ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return ANSI_ESCAPE.sub("", text)


def parse_grid(raw_text: str, start_chars=("S", "P", "@"), goal_chars=("E", "G", "*"),
               wall_chars=("#", "█", "░", "|", "-", "+", "■")):
    """Parse raw terminal text into a 2D grid, returning (grid, start, goal)."""
    clean = strip_ansi(raw_text)
    lines = [line.rstrip("\r\n") for line in clean.splitlines() if line.strip()]
    if not lines:
        return [], None, None

    start = None
    goal = None
    grid = []

    for r, line in enumerate(lines):
        row = list(line)
        for c, ch in enumerate(row):
            if ch in start_chars:
                start = (r, c)
            elif ch in goal_chars:
                goal = (r, c)
        grid.append(row)

    return grid, start, goal


def bfs_solve(grid, start, goal, wall_chars=("#", "█", "░", "|", "-", "+", "■")):
    """Find shortest path from start to goal in 2D grid.

    Returns: (path_coords, moves_wasd, moves_udlr)
    """
    if not start or not goal:
        return None, "", ""

    h = len(grid)
    w = max(len(row) for row in grid)

    # Directions: (dr, dc, wasd, udlr)
    dirs = [
        (-1, 0, "w", "U"),
        (1, 0, "s", "D"),
        (0, -1, "a", "L"),
        (0, 1, "d", "R"),
    ]

    queue = collections.deque([(start, [start], "", "")])
    visited = {start}

    while queue:
        (curr_r, curr_c), path, wasd, udlr = queue.popleft()
        if (curr_r, curr_c) == goal:
            return path, wasd, udlr

        for dr, dc, m_wasd, m_udlr in dirs:
            nr, nc = curr_r + dr, curr_c + dc
            if 0 <= nr < h and 0 <= nc < len(grid[nr]):
                ch = grid[nr][nc]
                if ch not in wall_chars and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append(((nr, nc), path + [(nr, nc)], wasd + m_wasd, udlr + m_udlr))

    return None, "", ""


def pipeline_commands(moves: str, separator="\n") -> bytes:
    """Format moves for pipelined single-burst socket transmission."""
    return separator.join(list(moves)).encode() + separator.encode()


def _self_test():
    # Synthetic ANSI-colored terminal maze
    raw_ansi_maze = (
        "\x1b[31m##########\x1b[0m\n"
        "\x1b[31m#\x1b[32mS\x1b[0m       \x1b[31m#\x1b[0m\n"
        "\x1b[31m#\x1b[0m ### ## \x1b[31m#\x1b[0m\n"
        "\x1b[31m#\x1b[0m   #   \x1b[33mE\x1b[31m#\x1b[0m\n"
        "\x1b[31m##########\x1b[0m\n"
    )

    clean = strip_ansi(raw_ansi_maze)
    assert "\x1b[" not in clean

    grid, start, goal = parse_grid(raw_ansi_maze)
    assert start == (1, 1), f"Expected start (1, 1), got {start}"
    assert goal == (3, 8), f"Expected goal (3, 8), got {goal}"

    path, wasd, udlr = bfs_solve(grid, start, goal)
    assert path is not None, "BFS failed to find path"
    assert len(path) == 10, f"Expected path length 10, got {len(path)}"
    assert wasd == "ddddssddd", f"Unexpected moves: {wasd}"

    pipelined = pipeline_commands(wasd)
    assert pipelined.startswith(b"d\n")

    print(f"[ok] ansi_maze_solver self-test passed (path length {len(path)}, moves={wasd})")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        _self_test()
    elif len(sys.argv) > 2 and sys.argv[1] == "solve":
        with open(sys.argv[2], "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        grid, start, goal = parse_grid(content)
        path, wasd, udlr = bfs_solve(grid, start, goal)
        if path:
            print(f"Start: {start}, Goal: {goal}, Steps: {len(path) - 1}")
            print(f"WASD: {wasd}")
            print(f"UDLR: {udlr}")
        else:
            print("No path found.")
    else:
        print(__doc__)
