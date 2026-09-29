import re
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import NamedTuple
from collections.abc import Iterator

CLEAR = "\033[H\033[J"
SIZE = 6
BLOCK = 3
QUAD = 2
WINNING_LINE = 5
DIRECTIONS = ((1, 1), (0, 1), (1, 0), (-1, 1))
Coord = tuple[int, int]

class PentagoError(Exception): ...

class ParseError(PentagoError): ...

class BoardError(PentagoError): ...

class RuleError(PentagoError): ...

class Sides(Enum):

    BLACK = auto()
    WHITE = auto()

class Orientation(Enum):

    CLOCKWISE = auto()
    COUNTERCLOCK = auto()

GLYPHS = {Sides.BLACK: "◯", Sides.WHITE: "●", None: "·"}
PLAYERS = {Sides.BLACK: "Pretas", Sides.WHITE: "Brancas"}
OPPONENT = {Sides.BLACK: Sides.WHITE, Sides.WHITE: Sides.BLACK}

@dataclass
class Board:

    matrix: list[list[None | Sides]]

    @classmethod
    def build_initial_board(cls) -> "Board":

        initial_board: list[list[Sides | None]] = [[None for _ in range(SIZE)] for _ in range(SIZE)]
        
        return cls(initial_board)

def in_bounds(cell: Coord) -> bool:

    row, col = cell

    return 0 <= row < SIZE and 0 <= col < SIZE

def valid_quadrant(cell: Coord) -> bool:

    row, col = cell

    return 0 <= row < QUAD and 0 <= col < QUAD

def ray(origin: Coord, step: Coord) -> Iterator[Coord]:

    row, col = origin
    dr, dc = step

    while in_bounds((row, col)):

        yield row, col

        row, col = row + dr, col + dc

def block_of(cell: Coord) -> Coord:

    row, col = cell

    return (row // BLOCK, col // BLOCK)

def local_of(cell: Coord) -> Coord:

    row, col = cell

    return row % BLOCK, col % BLOCK

def global_of(quadrant: Coord, local: Coord) -> Coord:

    return quadrant[0] * BLOCK + local[0], quadrant[1] * BLOCK + local[1]

def cells_of_block(quadrant: Coord) -> Iterator[Coord]:

    for local_r in range(BLOCK):

        for local_c in range(BLOCK):

            yield global_of(quadrant, (local_r, local_c))

class Move (NamedTuple):

    placement: Coord
    quadrant: Coord
    orientation: Orientation
    agent: Sides

def apply_placement(placement: Coord, agent: Sides, board: Board) -> None:

    r, c = placement
    board.matrix[r][c] = agent

def rotate_block(board: Board, quadrant: Coord, orientation: Orientation) -> None:

    extracted = [board.matrix[r][c] for r, c in cells_of_block(quadrant)]
    block = [extracted[i : i + BLOCK] for i in range(0, len(extracted), BLOCK)]

    if orientation == Orientation.CLOCKWISE:

        rotated = [list(row) for row in zip(*block[::-1])]

    elif orientation == Orientation.COUNTERCLOCK:

        rotated = [list(row) for row in zip(*block)][::-1]

    rotated_flat = [cell for row in rotated for cell in row]

    for (r, c), val in zip(cells_of_block(quadrant), rotated_flat):

        board.matrix[r][c] = val

def has_alignment(agent: Sides, board: Board) -> bool:

    for r in range(SIZE):
        
        for c in range(SIZE):

            for step in DIRECTIONS:

                count = 0

                for row, col in ray((r, c), step):

                    if board.matrix[row][col] is not agent:

                        break

                    count += 1

                    if count >= WINNING_LINE:

                        return True

    return False

def parse_input(board: Board, text: str) -> tuple[Coord, Coord, Orientation]:
    
    match = re.fullmatch(r'\s*([A-Za-z])\s*(\d)\s*([A-Za-z])\s*(\d)\s*([A-Za-z])\s*([A-Za-z])\s*', text)
    
    if match is None:
    
        raise ParseError("Input irreconhecível, tente (posição) + (quadrante) + (sentido horário ou anti-horário): [a-f][1-6] [A-B][1-2] [SH]/[AH].")
    
    placement = int(match.group(2)) - 1, ord(match.group(1).lower()) - ord('a')
    r, c = placement

    if not in_bounds((r, c)):
    
        raise BoardError(f"A dupla de coordenadas ({r + 1}, {c + 1}) não existe no tabuleiro.")
    
    if board.matrix[r][c] is not None:
            
        raise RuleError(f"A casa nas coordenadas ({r + 1}, {c + 1}) já está ocupada.")

    quadrant = ord(match.group(3).upper()) - ord('A'), int(match.group(4)) - 1

    if not valid_quadrant(quadrant):
            
        raise BoardError("Quadrante inválido, temos linha A e linha B + coluna 1 e coluna 2.")

    if (match.group(5).upper() + match.group(6).upper()) == "SH":

        orientation = Orientation.CLOCKWISE

    elif (match.group(5).upper() + match.group(6).upper()) == "AH":
    
        orientation = Orientation.COUNTERCLOCK

    else:
    
        raise ParseError(f"Orientação de giro inválida, tente SH (sentido horário) ou AH (anti-horário) no final.")
    
    return (placement, quadrant, orientation)

def ask_input(agent: Sides):

    jogada = str(input(f"{PLAYERS[agent]} jogam, insira [a-f][1-6] [A-B][1-2] [SH]/[AH]: "))

    return jogada

def render_row(row) -> str:

    left = " ".join(GLYPHS[cell] for cell in row[:BLOCK])
    right = " ".join(GLYPHS[cell] for cell in row[BLOCK:])

    return f"{left} | {right}"

def render_header() -> str:

    letters = [chr(ord("a") + col) for col in range(SIZE)]
    left = " ".join(letters[:BLOCK])
    right = " ".join(letters[BLOCK:])

    return f"   {left} | {right}"

def format_board(board: Board) -> str:

    lines = [render_header()]

    for row_idx, row in enumerate(board.matrix, start=1):

        if row_idx == BLOCK + 1:

            lines.append("   " + "-" * 13)

        lines.append(f"{row_idx:>2d} {render_row(row)}")

    return "\n".join(lines)

def print_board(board: Board):

    print(format_board(board))

def play_pentago():

    board = Board.build_initial_board()
    agent = Sides.WHITE

    while True:

        print(CLEAR, end="")
        print_board(board)
        print()

        try:
        
            play = ask_input(agent)
            placement, quadrant, orientation = parse_input(board, play)

        except PentagoError as e:
        
            print(e)
            time.sleep(2)
        
            continue

        apply_placement(placement, agent, board)
        print(CLEAR, end="")
        print_board(board)
        time.sleep(3)

        if has_alignment(agent, board):

            print(CLEAR, end="")
            print_board(board)
            print()
            print(f"O vencedor é o lado das {PLAYERS[agent]}.")
            
            break

        rotate_block(board, quadrant, orientation)

        black = has_alignment(Sides.BLACK, board)
        white = has_alignment(Sides.WHITE, board)

        if black and white:

            print(CLEAR, end="")
            print_board(board)
            print()
            print(f"Dois alinhamentos simultâneos. O resultado é um empate.")

            break

        elif black:
        
            print(CLEAR, end="")
            print_board(board)
            print()
            print(f"O vencedor é o lado das {PLAYERS[Sides.BLACK]}.")

            break

        elif white:
                    
            print(CLEAR, end="")
            print_board(board)
            print()
            print(f"O vencedor é o lado das {PLAYERS[Sides.WHITE]}.")

            break

        elif all(cell is not None for row in board.matrix for cell in row):

            print(CLEAR, end="")
            print_board(board)
            print()
            print(f"O board foi preenchido e girado sem produzir vencedor. O resultado é um empate.")

            break

        agent = OPPONENT[agent]

if __name__ == "__main__":

    play_pentago()