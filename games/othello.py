import re
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import NamedTuple
from collections.abc import Iterator

CLEAR = "\033[H\033[J"
SIZE = 8
DIRECTIONS = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0))
Cell = tuple[int, int]

class OthelloError(Exception):

    ...

class ParseError(OthelloError):

    ...

class BoardError(OthelloError):

    ...

class Overlap(OthelloError):

    ...

class RuleError(OthelloError):

    ...

class Sides(Enum):

    BLACK = auto()
    WHITE = auto()

GLYPHS = {Sides.BLACK: "◯", Sides.WHITE: "●", None: "·"}
PLAYERS = {Sides.BLACK: "Pretas", Sides.WHITE: "Brancas"}
OPPONENT = {Sides.BLACK: Sides.WHITE, Sides.WHITE: Sides.BLACK}

def in_bounds(cell: Cell) -> bool:

    row, col = cell

    return 0 <= row < SIZE and 0 <= col < SIZE

@dataclass
class Board:

    matrix: list[list[None | Sides]]

    @classmethod
    def build_initial_board(cls) -> "Board":

        initial_board: list[list[Sides | None]] = [[None for _ in range(SIZE)] for _ in range(SIZE)]
        initial_board[3][3], initial_board[4][4] = Sides.WHITE, Sides.WHITE
        initial_board[4][3], initial_board[3][4] = Sides.BLACK, Sides.BLACK
        
        return cls(initial_board)

class Move (NamedTuple):

    origin: Cell
    agent: Sides

def ray(origin: Cell, step: Cell) -> Iterator[Cell]:

    row, col = origin
    dr, dc = step

    row, col = row + dr, col + dc

    while in_bounds((row, col)):

        yield row, col

        row, col = row + dr, col + dc

def is_legal(move: Move, board: Board) -> bool:

    if not in_bounds(move.origin):

        return False
        
    r, c = move.origin

    return board.matrix[r][c] is None and bool(flips(move, board))

def flips(move: Move, board: Board) -> tuple[Cell, ...]:

    opponent = OPPONENT[move.agent]
    flipped = []

    for step in DIRECTIONS:

        potential_flips = []

        for r, c in ray(move.origin, step):

            piece = board.matrix[r][c]

            if piece is opponent:

                potential_flips.append((r, c))

            elif piece is None:

                break

            elif piece is move.agent:

                flipped.extend(potential_flips)

                break
                
    return tuple(flipped)

def legal_moves(agent: Sides, board: Board) -> Iterator[Move]:

    for r in range(SIZE):

        for c in range(SIZE):

            move = Move((r, c), agent)

            if is_legal(move, board):

                yield move

def apply_move(move: Move, board: Board) -> None:

    r, c = move.origin

    if not in_bounds((r, c)):

        raise BoardError(f"A dupla de coordenadas ({r + 1}, {c + 1}) não existe no tabuleiro.")

    if board.matrix[r][c] is not None:
        
        raise Overlap(f"A casa nas coordenadas ({r + 1}, {c + 1}) já está ocupada.")

    flipped_pieces = flips(move, board)

    if not flipped_pieces:

        raise RuleError(f"A jogada em ({r + 1}, {c + 1}) não flanqueia peças adversárias.")

    board.matrix[r][c] = move.agent

    for f_r, f_c in flipped_pieces:

        board.matrix[f_r][f_c] = move.agent

def has_legal_moves(agent: Sides, board: Board) -> bool:

    return any(True for _ in legal_moves(agent, board))

def game_over(board: Board) -> bool:

    return not (has_legal_moves(Sides.BLACK, board) or has_legal_moves(Sides.WHITE, board))

def count_scores(board: Board)-> dict[Sides, int]:

    scores = {Sides.BLACK: 0, Sides.WHITE: 0}

    for r in range(SIZE):
    
            for c in range(SIZE):
    
                if board.matrix[r][c] is Sides.BLACK:

                    scores[Sides.BLACK] += 1

                if board.matrix[r][c] is Sides.WHITE:
                
                    scores[Sides.WHITE] += 1

    return scores

def game_result(board: Board) -> Sides | None:

    scores = count_scores(board)

    if scores[Sides.BLACK] > scores[Sides.WHITE]:

        return Sides.BLACK

    elif scores[Sides.WHITE] > scores[Sides.BLACK]:

        return Sides.WHITE

    else:

        return None

def parse_input(text: str) -> Cell:
    
    match = re.fullmatch(r'\s*([A-Za-z])\s*(\d)\s*', text)
    
    if match is None:
    
        raise ParseError("Input de jogada irreconhecível, tente [a-h][1-8].")
    
    row, col = int(match.group(2)) - 1, ord(match.group(1).upper()) - ord('A')
    
    return row, col

def ask_input(agent: Sides) -> str:

    jogada = str(input(f"{PLAYERS[agent]} jogam, insira [a-h][1-8]: "))

    return jogada

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

def play_othello():

    board = Board.build_initial_board()
    agent = Sides.BLACK

    while True:

        print(CLEAR, end="")
        print_board(board)
        print()

        scores = count_scores(board)

        print(f"Score das {PLAYERS[Sides.BLACK]}: {scores[Sides.BLACK]}")
        print(f"Score das {PLAYERS[Sides.WHITE]}: {scores[Sides.WHITE]}")
        print()

        if has_legal_moves(agent, board):

            try:
            
                play = ask_input(agent)
                row, col = parse_input(play)
                move = Move((row, col), agent)
                apply_move(move, board)
                scores = count_scores(board)

            except OthelloError as e:
            
                print(e)
                time.sleep(3)
            
                continue

        elif game_over(board):

            winner = game_result(board)

            if winner is Sides.BLACK or winner is Sides.WHITE:

                print(CLEAR, end="")
                print_board(board)
                print()
                print(f"O vencedor é o lado das {PLAYERS[winner]} por {scores[winner] - scores[OPPONENT[winner]]} pontos.")
                
                break

            else:

                print(CLEAR, end="")
                print_board(board)
                print()
                print(f"O resultado é um empate.")

        else:

            print(CLEAR, end="")
            print_board(board)
            print()
            print(f"As {PLAYERS[agent]} não têm jogadas, a vez será passada para as {PLAYERS[OPPONENT[agent]]}.")

        agent = OPPONENT[agent]

if __name__ == "__main__":

    play_othello()