import re
import time
import random
from enum import Enum, auto
from typing import NamedTuple
from collections.abc import Iterator, Iterable
from dataclasses import dataclass

CLEAR = "\033[H\033[J"
BOARD_SIZE = 8
QUADRANT_SIZE = 4
QUAD_COORD_SIZE = 2
WINNING_LINE = 5
CAPTURE_LINE = 4
VECTOR_VALUES: tuple[int, int, int] = (1, 0, -1)
DIRECTIONS: Iterable = tuple((dr, dc) for dr in VECTOR_VALUES for dc in VECTOR_VALUES if (dr, dc) != (0, 0))
Coord = tuple[int, int]

class PentwisteError(Exception): ...

class ParseError(PentwisteError): ...

class BoardError(PentwisteError): ...

class RuleError(PentwisteError): ...

class Sides(Enum):

    BLACK = auto()
    WHITE = auto()

class Orientation(Enum):

    CLOCKWISE = auto()
    COUNTERCLOCK = auto()

SIDES = [Sides.BLACK, Sides.WHITE]
GLYPHS = {Sides.BLACK: "◯", Sides.WHITE: "●", None: "·"}
PLAYERS = {Sides.BLACK: "Pretas", Sides.WHITE: "Brancas"}
OPPONENT = {Sides.BLACK: Sides.WHITE, Sides.WHITE: Sides.BLACK}
QUADRANTS = {(0, 0): "A1", (0, 1): "A2", (1, 0): "B1", (1, 1): "B2"}
ORIENTATIONS = {Orientation.CLOCKWISE: "Sentido Horário", Orientation.COUNTERCLOCK: "Sentido Anti-Horário"}

@dataclass
class Board:

    matrix: list[list[Sides | None]]

    @classmethod
    def build_initial_board(cls) -> "Board":

        matrix: list[list[Sides | None]] = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

        return cls(matrix)

def in_bounds(cell: Coord) -> bool:

    row, col = cell

    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

def valid_quadrant(cell: Coord) -> bool:

    row, col = cell

    return 0 <= row < QUAD_COORD_SIZE and 0 <= col < QUAD_COORD_SIZE

def span(origin: Coord, step: Coord) -> Iterator[Coord]:

    row, col = origin
    dr, dc = step

    while in_bounds((row, col)):

        yield row, col

        row, col = row + dr, col + dc

def which_quadrant(coord: Coord) -> Coord:

    row, col = coord

    return (row // QUADRANT_SIZE, col // QUADRANT_SIZE)

def local_coord(coord: Coord) -> Coord:

    row, col = coord

    return (row % QUADRANT_SIZE, col % QUADRANT_SIZE)

def global_coord(quadrant: Coord, local: Coord) -> Coord:

    return quadrant[0] * QUADRANT_SIZE + local[0], quadrant[1] * QUADRANT_SIZE + local[1]

def global_coords_of_quadrant(quadrant: Coord) -> Iterator[Coord]:

    for local_r in range(QUADRANT_SIZE):

        for local_c in range(QUADRANT_SIZE):

            yield global_coord(quadrant, (local_r, local_c))

class Move (NamedTuple):

    placement: Coord
    quadrant: Coord
    orientation: Orientation
    agent: Sides

def apply_placement(placement: Coord, agent: Sides, board: Board) -> None:

    r, c = placement
    board.matrix[r][c] = agent

def rotate_quadrant(board: Board, quadrant: Coord, orientation: Orientation) -> None:

    extracted_quadrant = [board.matrix[r][c] for r, c in global_coords_of_quadrant(quadrant)]
    quadrant_matrix = [extracted_quadrant[i : i + QUADRANT_SIZE] for i in range(0, len(extracted_quadrant), QUADRANT_SIZE)]

    if orientation == Orientation.CLOCKWISE:
    
        rotated = [list(row) for row in zip(*quadrant_matrix[::-1])]

    if orientation == Orientation.COUNTERCLOCK:
        
        rotated = [list(row) for row in zip(*quadrant_matrix)][::-1]

    rotated_flat = [cell for row in rotated for cell in row]

    for (r, c), new_value in zip(global_coords_of_quadrant(quadrant), rotated_flat):
    
        board.matrix[r][c] = new_value

def placement_captures(placement: Coord, agent: Sides, board: Board) -> int:

    captured_pairs = 0
    r, c = placement

    for dr, dc in DIRECTIONS:

        r1, c1 = r + dr * 1, c + dc * 1
        r2, c2 = r + dr * 2, c + dc * 2
        r3, c3 = r + dr * 3, c + dc * 3

        if not in_bounds((r3, c3)):
        
            continue

        if (board.matrix[r1][c1] is OPPONENT[agent] and
            board.matrix[r2][c2] is OPPONENT[agent] and
            board.matrix[r3][c3] is agent):

            board.matrix[r1][c1] = None
            board.matrix[r2][c2] = None
            captured_pairs += 1

    return captured_pairs

def rotation_captures(quadrant: Coord, board: Board) -> dict[Sides, int]:

    captured_pairs = {side: [] for side in SIDES}

    for r, c in global_coords_of_quadrant(quadrant):

        agent = board.matrix[r][c]

        if agent is None:

            continue

        for dr, dc in DIRECTIONS:

            r1, c1 = r + dr * 1, c + dc * 1
            r2, c2 = r + dr * 2, c + dc * 2
            r3, c3 = r + dr * 3, c + dc * 3

            if not in_bounds((r3, c3)):

                continue

            cells = ((r, c), (r1, c1), (r2, c2), (r3, c3))

            if all(which_quadrant(cell) == quadrant for cell in cells):

                continue

            if (board.matrix[r1][c1] is OPPONENT[agent] and
                board.matrix[r2][c2] is OPPONENT[agent] and
                board.matrix[r3][c3] is agent):

                captured_pairs[agent].append(((r1, c1), (r2, c2)))

    for pairs in captured_pairs.values():

        for (r1, c1), (r2, c2) in pairs:

            board.matrix[r1][c1] = None
            board.matrix[r2][c2] = None

    return {side: len(pairs) for side, pairs in captured_pairs.items()}

def has_alignment(agent: Sides, board: Board) -> bool:

    for r in range(BOARD_SIZE):
        
        for c in range(BOARD_SIZE):

            for step in DIRECTIONS:

                count = 0

                for row, col in span((r, c), step):

                    if board.matrix[row][col] is not agent:

                        break

                    count += 1

                    if count >= WINNING_LINE:

                        return True

    return False

def check_win(captured_pairs: int, agent: Sides, board: Board) -> bool:

    return has_alignment(agent, board) or captured_pairs >= 4

def full_board(board: Board) -> bool:

    return all(cell is not None for row in board.matrix for cell in row)

def parse_input(board: Board, text: str) -> tuple[Coord, Coord, Orientation]:
    
    match = re.fullmatch(r'\s*([A-Za-z])\s*(\d)\s*([A-Za-z])\s*(\d)\s*([A-Za-z])\s*([A-Za-z])\s*', text)
    
    if match is None:
    
        raise ParseError("Input irreconhecível, tente (posição) + (quadrante) + (sentido horário ou anti-horário): [a-g][1-8] [A-B][1-2] [SH]/[AH].")
    
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

    jogada = str(input(f"{PLAYERS[agent]} jogam, insira [a-h][1-8] [A-B][1-2] [SH]/[AH]: "))

    return jogada

def render_row(row) -> str:

    left = " ".join(GLYPHS[cell] for cell in row[:QUADRANT_SIZE])
    right = " ".join(GLYPHS[cell] for cell in row[QUADRANT_SIZE:])

    return f"{left} | {right}"

def render_header() -> str:

    letters = [chr(ord("a") + col) for col in range(BOARD_SIZE)]
    left = " ".join(letters[:QUADRANT_SIZE])
    right = " ".join(letters[QUADRANT_SIZE:])

    return f"   {left}   {right}"

def format_board(board: Board) -> str:

    lines = [render_header()]

    for row_idx, row in enumerate(board.matrix, start=1):

        if row_idx == QUADRANT_SIZE + 1:

            lines.append("   " + "-" * 17)

        lines.append(f"{row_idx:>2d} {render_row(row)}")

    return "\n".join(lines)

def print_board(board: Board):

    print(format_board(board))

def play_pentwiste():

    board = Board.build_initial_board()
    agent = random.choice(SIDES)
    scores = {Sides.BLACK: 0, Sides.WHITE: 0}

    while True:
    
        print(CLEAR, end="")
        print_board(board)
        print()
        print(f"Score das {PLAYERS[Sides.BLACK]}: {scores[Sides.BLACK]}")
        print(f"Score das {PLAYERS[Sides.WHITE]}: {scores[Sides.WHITE]}")
        print()

        try:
        
            play = ask_input(agent)
            placement, quadrant, orientation = parse_input(board, play)

        except PentwisteError as e:
        
            print(e)
            time.sleep(2)
        
            continue

        apply_placement(placement, agent, board)
        scores[agent] += placement_captures(placement, agent, board)

        print(CLEAR, end="")
        print_board(board)
        print()
        print(f"Score das {PLAYERS[Sides.BLACK]}: {scores[Sides.BLACK]}")
        print(f"Score das {PLAYERS[Sides.WHITE]}: {scores[Sides.WHITE]}")

        time.sleep(3)

        if check_win(scores[agent], agent, board):
        
            print(CLEAR, end="")
            print_board(board)
            print()
            print(f"Score das {PLAYERS[Sides.BLACK]}: {scores[Sides.BLACK]}")
            print(f"Score das {PLAYERS[Sides.WHITE]}: {scores[Sides.WHITE]}")
            print()
            print(f"O vencedor é o lado das {PLAYERS[agent]}.")

            time.sleep(3)
            
            break

        rotate_quadrant(board, quadrant, orientation)

        captures = rotation_captures(quadrant, board)
        scores[Sides.BLACK] += captures[Sides.BLACK]
        scores[Sides.WHITE] += captures[Sides.WHITE]

        black = check_win(scores[Sides.BLACK], Sides.BLACK, board)
        white = check_win(scores[Sides.WHITE], Sides.WHITE, board)

        if black and white:
        
            print(CLEAR, end="")
            print_board(board)
            print()
            print(f"Score das {PLAYERS[Sides.BLACK]}: {scores[Sides.BLACK]}")
            print(f"Score das {PLAYERS[Sides.WHITE]}: {scores[Sides.WHITE]}")
            print()
            print(f"Dois condições de vitória simultâneas. O resultado é um empate.")

            time.sleep(3)

            break

        elif black:
        
            print(CLEAR, end="")
            print_board(board)
            print()
            print(f"Score das {PLAYERS[Sides.BLACK]}: {scores[Sides.BLACK]}")
            print(f"Score das {PLAYERS[Sides.WHITE]}: {scores[Sides.WHITE]}")
            print()
            print(f"O vencedor é o lado das {PLAYERS[Sides.BLACK]}.")

            time.sleep(3)

            break

        elif white:
                    
            print(CLEAR, end="")
            print_board(board)
            print()
            print(f"Score das {PLAYERS[Sides.BLACK]}: {scores[Sides.BLACK]}")
            print(f"Score das {PLAYERS[Sides.WHITE]}: {scores[Sides.WHITE]}")
            print()
            print(f"O vencedor é o lado das {PLAYERS[Sides.WHITE]}.")

            time.sleep(3)

            break

        elif full_board(board):

            print(CLEAR, end="")
            print_board(board)
            print()
            print(f"Score das {PLAYERS[Sides.BLACK]}: {scores[Sides.BLACK]}")
            print(f"Score das {PLAYERS[Sides.WHITE]}: {scores[Sides.WHITE]}")
            print()
            print(f"O tabuleiro foi preenchido e rotacionado sem produzir vencedor. O resultado é um empate.")

            time.sleep(3)

            break

        agent = OPPONENT[agent]

if __name__ == "__main__":

    play_pentwiste()