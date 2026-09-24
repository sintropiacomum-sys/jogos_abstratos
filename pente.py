from dataclasses import dataclass
import re
import time
import random
from enum import Enum, auto
from typing import NamedTuple

CLEAR = "\033[H\033[J"
SIZE = 18
WINNING_LINE = 5
CAPTURE_SPAN = 4
DIRECTIONS = ((1, 1), (0, 1), (1, 0), (-1, 1))

class PenteError(Exception):
    
    ...

class Sides(Enum):

    BLACK = auto()
    WHITE = auto()

SIDES = [Sides.BLACK, Sides.WHITE]
GLYPHS = {Sides.BLACK: "◯", Sides.WHITE: "●", None: "·"}
PLAYERS = {Sides.BLACK: "Pretas", Sides.WHITE: "Brancas"}
OPPONENT = {Sides.BLACK: Sides.WHITE, Sides.WHITE: Sides.BLACK}

def in_bounds(row, col) -> bool:

    return 0 <= row < SIZE and 0 <= col < SIZE

@dataclass
class Board:

    matrix: list[list[None | Sides]]

    @classmethod
    def build_initial_board(cls) -> "Board":

        initial_board: list[list[Sides | None]] = [[None for _ in range(SIZE)] for _ in range(SIZE)]
        
        return cls(initial_board)

class Move (NamedTuple):

    row: int
    col: int
    agent: Sides

def parse_input(board: Board, text: str):
    
    match = re.fullmatch(r'\s*([A-Za-z])\s*(\d{1,2})\s*', text)
    
    if match is None:
    
        raise PenteError("Input de jogada irreconhecível, tente [a-r][1-18].")
    
    row, col = int(match.group(2)) - 1, ord(match.group(1).lower()) - ord('a')

    if not in_bounds(row, col):

        raise PenteError("Jogada fora das coordenadas do tabuleiro.")
    
    if board.matrix[row][col] is not None:

        raise PenteError("Posição já ocupada.")
    
    return row, col

def ask_input(agent: Sides):

    play = str(input(f"{PLAYERS[agent]} jogam, insira [a-r][1-18]: "))

    return play

def apply_move(move: Move, board: Board):

    board.matrix[move.row][move.col] = move.agent

def captures(move: Move, board: Board) -> int:

    captured_pairs = 0

    for dr, dc in DIRECTIONS:

        for multiplier in (1, -1):

            step_r, step_c = dr * multiplier, dc * multiplier

            r1, c1 = move.row + step_r * 1, move.col + step_c * 1
            r2, c2 = move.row + step_r * 2, move.col + step_c * 2
            r3, c3 = move.row + step_r * 3, move.col + step_c * 3

            if (board.matrix[r1][c1] is OPPONENT[move.agent] and
                board.matrix[r2][c2] is OPPONENT[move.agent] and
                board.matrix[r3][c3] is move.agent):

                board.matrix[r1][c1] = None
                board.matrix[r2][c2] = None
                captured_pairs += 1

    return captured_pairs

def check_alignment(move: Move, board: Board) -> bool:

    for dr, dc in DIRECTIONS:

        for multiplier in (1, -1):

            count = 1

            r, c = move.row + dr * multiplier, move.col + dc * multiplier

            while in_bounds(r, c) and board.matrix[r][c] is move.agent:

                count += 1
                r += dr
                c += dc

            if count >= WINNING_LINE:

                return True

    return False

def check_win(captured_pairs: int, move: Move, board: Board) -> bool:

    return check_alignment(move, board) or captured_pairs >= 5

def render_row(row) -> str:

    return " ".join(GLYPHS[col] for col in row)

def format_board(board: Board) -> str:

    header = "   " + " ".join(chr(ord("a") + col) for col in range(SIZE))
    
    lines = [header]

    for row_idx, row in enumerate(board.matrix, start=1):

        rendered_row = render_row(row)

        lines.append(f"{row_idx:>2d} {rendered_row}")

    return "\n".join(lines)

def print_board(board: Board):

    print(format_board(board))

def play_pente():

    board = Board.build_initial_board()
    agent = random.choice(SIDES)
    scores = {Sides.BLACK: 0, Sides.WHITE: 0}
    apply_move(Move(8, 8, agent), board)
    agent = OPPONENT[agent]

    while True:

        print(CLEAR, end="")

        print_board(board)
        print()
        print(f"Score das {PLAYERS[Sides.BLACK]}: {scores[Sides.BLACK]}")
        print(f"Score das {PLAYERS[Sides.WHITE]}: {scores[Sides.WHITE]}")
        print()

        try:

            play = ask_input(agent)
            row, col = parse_input(board, play)
            move = Move(row, col, agent)
            apply_move(move, board)
            scores[agent] += captures(move, board)
            
        except PenteError as e:

            print(e)
            time.sleep(3)

            continue

        if check_win(scores[agent], move, board):

            print(CLEAR, end="")
            print_board(board)
            print()
            print(f"O vencedor é o lado das {PLAYERS[agent]}.")

            break

        agent = OPPONENT[agent]

if __name__ == "__main__":

    play_pente()