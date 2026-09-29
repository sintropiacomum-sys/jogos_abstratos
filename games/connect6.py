from dataclasses import dataclass
import re
import time
from enum import Enum, auto
from typing import NamedTuple

CLEAR = "\033[H\033[J"
BOARD_SIZE = 19
WINNING_LINE = 6
DIRECTIONS = ((1, 1), (0, 1), (1, 0), (-1, 1))

class Connect6Error(Exception):
    
    ...

class Sides(Enum):

    BLACK = auto()
    WHITE = auto()

GLYPHS = {Sides.BLACK: "◯", Sides.WHITE: "●", None: "·"}
PLAYERS = {Sides.BLACK: "Pretas", Sides.WHITE: "Brancas"}
OPPONTENT = {Sides.BLACK: Sides.WHITE, Sides.WHITE: Sides.BLACK}

def in_bounds(row, col) -> bool:

    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

@dataclass
class Board:

    matrix: list[list[None | Sides]]

    @classmethod
    def build_initial_board(cls) -> "Board":

        initial_board: list[list[Sides | None]] = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        
        return cls(initial_board)

class Move (NamedTuple):

    row: int
    col: int
    agent: Sides

def parse_input(board: Board, text: str):
    
    match = re.fullmatch(r'\s*([A-Za-z])\s*(\d{1,2})\s*', text)
    
    if match is None:
    
        raise Connect6Error("Input de jogada irreconhecível, tente [A-S][1-19].")
    
    row, col = int(match.group(2)) - 1, ord(match.group(1).upper()) - ord('A')

    if not in_bounds(row, col):
    
        raise Connect6Error("Jogada fora das coordenadas do tabuleiro.")
        
    if board.matrix[row][col] is not None:

        raise Connect6Error("Posição já ocupada.")
    
    return row, col

def ask_input(agent: Sides):

    jogada = str(input(f"{PLAYERS[agent]} jogam, insira [A-S][1-19]: "))

    return jogada

def apply_move(move: Move, board: Board):

    board.matrix[move.row][move.col] = move.agent

def check_alignment(move: Move, board: Board) -> bool:

    for dr, dc in DIRECTIONS:

        count = 1

        for multiplier in (1, -1):

            r, c = move.row + dr * multiplier, move.col + dc * multiplier

            while in_bounds(r, c) and board.matrix[r][c] is move.agent:

                count += 1
                r += dr * multiplier
                c += dc * multiplier

        if count >= WINNING_LINE:

            return True

    return False

def full_board(number_plays: int) -> bool:

    return number_plays >= 361

def render_row(row) -> str:
    
    return " ".join(GLYPHS[col] for col in row)

def format_board(board: Board) -> str:

    header = "   " + " ".join(chr(ord("A") + col) for col in range(BOARD_SIZE))
    
    lines = [header]

    for row_idx, row in enumerate(board.matrix, start=1):

        rendered_row = render_row(row)

        lines.append(f"{row_idx:>2d} {rendered_row}")

    return "\n".join(lines)

def print_board(board: Board):

    print(format_board(board))

def play_connect6():

    agent = Sides.BLACK
    board = Board.build_initial_board()
    plays = 0

    while True:

        print(CLEAR, end="")
        print_board(board)
        print()

        try:

            play = ask_input(agent)
            row, col = parse_input(board, play)
            move = Move(row, col, agent)
            apply_move(move, board)
            plays += 1

        except Connect6Error as e:

            print(e)
            time.sleep(3)

            continue

        if check_alignment(move, board):

            print(CLEAR, end="")
            print_board(board)
            print()
            print(f"O vencedor é o lado das {PLAYERS[agent]}.")

            break

        if full_board(plays):

            print(CLEAR, end="")
            print_board(board)
            print()
            print(f"Tabuleiro cheio sem produzir vencedor. O resultado é um empate.")

        agent = OPPONTENT[agent]

if __name__ == "__main__":

    play_connect6()