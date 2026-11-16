#!/usr/bin/env python3
"""Notation and Protocol Steganography Helper for CTF.

Handles data hidden in structured notation and protocol headers:
1. Chess PGN Steganography (e.g. L3akCTF 'Blunder'):
   - Tracks destination squares of specific pieces (e.g. White Queen)
   - Plots destination squares onto an 8x8 board to reveal drawn letterforms / ASCII art
2. Protocol Header Covert Channels (e.g. CCSDS / TCP / IP):
   - Extracts ASCII from out-of-range, reserved, or anomalous header fields

Usage:
    python3 -I notation_stego.py pgn games.pgn --piece Q --color white
    python3 -I notation_stego.py --test
"""
import re
import sys


def parse_pgn_games(pgn_text: str):
    """Split PGN text into individual games."""
    # Games usually separated by multiple newlines or [Event ...] headers
    raw_games = re.split(r"(?=\[Event\s)", pgn_text)
    return [g.strip() for g in raw_games if g.strip()]


def extract_piece_destinations(game_pgn: str, piece="Q", color="white"):
    """Extract destination squares for a specific piece and color in a PGN game.

    piece: 'Q', 'K', 'R', 'B', 'N', or '' (pawn)
    color: 'white' or 'black'
    """
    # Remove metadata headers [Key "Value"]
    moves_text = re.sub(r"\[.*?\]", "", game_pgn)
    # Remove comments { ... }
    moves_text = re.sub(r"\{.*?\}", "", moves_text)
    # Remove game result (1-0, 0-1, 1/2-1/2, *)
    moves_text = re.sub(r"(1-0|0-1|1/2-1/2|\*)", "", moves_text)

    # Tokenize moves, skipping move numbers like '1.', '1...', etc.
    tokens = [t for t in moves_text.split() if not re.match(r"^\d+\.+", t)]

    # White moves are at even indices (0, 2, 4...), Black at odd (1, 3, 5...)
    moves = tokens[0::2] if color.lower() == "white" else tokens[1::2]
    destinations = []

    for move in moves:
        clean_move = move.rstrip("+#?!")
        # Match piece moves: e.g. Qd4, Qxe4, Q1a5, etc.
        if piece:
            pat = rf"^{piece}[a-h1-8]?x?([a-h][1-8])$"
        else:
            pat = r"^x?([a-h][1-8])$"

        m = re.match(pat, clean_move)
        if m:
            destinations.append(m.group(1))

    return destinations


def render_board(squares, on_char="█", off_char="."):
    """Render an 8x8 chessboard with marked destination squares.

    Rank 8 is at top (row 0), rank 1 at bottom (row 7).
    File 'a' is col 0, file 'h' is col 7.
    """
    board = [[off_char for _ in range(8)] for _ in range(8)]
    for sq in squares:
        if len(sq) == 2 and sq[0] in "abcdefgh" and sq[1] in "12345678":
            col = ord(sq[0]) - ord("a")
            row = 8 - int(sq[1])
            board[row][col] = on_char

    return "\n".join("".join(row) for row in board)


def decode_covert_fields(values, threshold=7):
    """Extract printable ASCII from numeric fields exceeding normal range."""
    chars = []
    for v in values:
        if v > threshold and 32 <= v <= 126:
            chars.append(chr(v))
    return "".join(chars)


def _self_test():
    # Synthetic PGN where White queen moves draw the letter 'H'
    # 'H' on 8x8:
    # rank 6: b, f
    # rank 5: b, f
    # rank 4: b, c, d, e, f
    # rank 3: b, f
    # rank 2: b, f
    fake_pgn = """
    [Event "Test CTF"]
    1. e4 e5 2. Qb6 a6 3. Qb5 a5 4. Qb4 a4 5. Qc4 a3 6. Qd4 h6 7. Qe4 h5 8. Qf4 h4 9. Qf6 h3 10. Qf5 g6 11. Qf3 g5 12. Qb3 g4 13. Qb2 g3 14. Qf2 1-0
    """
    dest = extract_piece_destinations(fake_pgn, piece="Q", color="white")
    assert len(dest) == 13, f"Expected 13 queen moves, got {len(dest)}: {dest}"

    rendered = render_board(dest, on_char="#", off_char=".")
    assert "#" in rendered
    assert len(rendered.splitlines()) == 8

    # Test covert protocol field decoding
    sample_fields = [1, 2, 0, 70, 76, 65, 71, 0, 3]  # 70='F', 76='L', 65='A', 71='G'
    decoded = decode_covert_fields(sample_fields, threshold=7)
    assert decoded == "FLAG", f"Covert field decode mismatch: {decoded}"

    print(f"[ok] notation_stego self-test passed: PGN moves parsed ({len(dest)} moves), covert fields={decoded}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        _self_test()
    elif len(sys.argv) > 2 and sys.argv[1] == "pgn":
        with open(sys.argv[2], "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        games = parse_pgn_games(content)
        print(f"Loaded {len(games)} game(s).")
        for i, g in enumerate(games):
            dest = extract_piece_destinations(g, piece="Q", color="white")
            print(f"--- Game {i+1} ({len(dest)} moves) ---")
            print(render_board(dest))
    else:
        print(__doc__)
