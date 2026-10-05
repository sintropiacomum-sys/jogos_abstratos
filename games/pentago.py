import re
from enum import Enum, auto
from typing import NamedTuple
from collections.abc import Iterator
from dataclasses import dataclass
from two_player_game import TwoPlayerGame, GameError, play_in_terminal

BOARD_SIZE = 6
BLOCK_SIZE = 3
QUADS_SIZE = 2
WINNING_LINE = 5
DIRECTIONS = ((1, 1), (0, 1), (1, 0), (-1, 1))
Coord = tuple[int, int]

class PentagoError(GameError): ...

class ParseError(PentagoError): ...

class BoardError(PentagoError): ...

class RuleError(PentagoError): ...

class Sides(Enum):

    BLACK = "Pretas"
    WHITE = "Brancas"

class Orientation(Enum):

    CLOCKWISE = auto()
    COUNTERCLOCK = auto()

GLYPHS = {Sides.BLACK: "◯", Sides.WHITE: "●", None: "·"}
OPPONENT = {Sides.BLACK: Sides.WHITE, Sides.WHITE: Sides.BLACK}

@dataclass
class Board:

    matrix: list[list[None | Sides]]

    def get_at(self, coord: Coord) -> Sides | None:
                
        r, c = coord
    
        return self.matrix[r][c]
        
    def set_at(self, coord: Coord, cell: Sides | None):
    
        r, c = coord
        self.matrix[r][c] = cell

    def copy(self) -> "Board":
    
        new_matrix = [row.copy() for row in self.matrix]

        return Board(new_matrix)

    @classmethod
    def build_initial_board(cls) -> "Board":

        initial_board: list[list[Sides | None]] = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        
        return cls(initial_board)

def in_bounds(cell: Coord) -> bool:

    row, col = cell

    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

def valid_quadrant(cell: Coord) -> bool:

    row, col = cell

    return 0 <= row < QUADS_SIZE and 0 <= col < QUADS_SIZE

def ray(origin: Coord, step: Coord) -> Iterator[Coord]:

    row, col = origin
    dr, dc = step

    while in_bounds((row, col)):

        yield row, col

        row, col = row + dr, col + dc

def which_quadrant(cell: Coord) -> Coord:

    row, col = cell

    return (row // BLOCK_SIZE, col // BLOCK_SIZE)

def local_coords(cell: Coord) -> Coord:

    row, col = cell

    return row % BLOCK_SIZE, col % BLOCK_SIZE

def global_coords(quadrant: Coord, local: Coord) -> Coord:

    return quadrant[0] * BLOCK_SIZE + local[0], quadrant[1] * BLOCK_SIZE + local[1]

def cells_of_block(quadrant: Coord) -> Iterator[Coord]:

    for local_r in range(BLOCK_SIZE):

        for local_c in range(BLOCK_SIZE):

            yield global_coords(quadrant, (local_r, local_c))

class Move (NamedTuple):

    placement: Coord
    quadrant: Coord
    orientation: Orientation
    agent: Sides

@dataclass
class GameState:

    board: Board
    agent: Sides

def generate_legal_moves(state: GameState) -> Iterator[Move]:

    for r_placement in range(BOARD_SIZE):

        for c_placement in range(BOARD_SIZE):

            placement = (r_placement, c_placement)

            if state.board.get_at(placement) is not None:

                continue

            for r_quadrant in range(QUADS_SIZE):

                for c_quadrant in range(QUADS_SIZE):

                    quadrant = (r_quadrant, c_quadrant)

                    for orientation in Orientation:

                        yield Move(placement, quadrant, orientation, state.agent)

def place_stone(placement: Coord, agent: Sides, board: Board) -> None:

    r, c = placement
    board.set_at((r, c), agent)

def rotate_block(board: Board, quadrant: Coord, orientation: Orientation) -> None:

    extracted = [board.matrix[r][c] for r, c in cells_of_block(quadrant)]
    block = [extracted[i : i + BLOCK_SIZE] for i in range(0, len(extracted), BLOCK_SIZE)]

    if orientation == Orientation.CLOCKWISE:

        rotated = [list(row) for row in zip(*block[::-1])]

    elif orientation == Orientation.COUNTERCLOCK:

        rotated = [list(row) for row in zip(*block)][::-1]

    rotated_flat = [cell for row in rotated for cell in row]

    for (r, c), val in zip(cells_of_block(quadrant), rotated_flat):

        board.matrix[r][c] = val

def has_alignment(agent: Sides, board: Board) -> bool:

    for r in range(BOARD_SIZE):
        
        for c in range(BOARD_SIZE):

            for step in DIRECTIONS:

                count = 0

                for row, col in ray((r, c), step):

                    if board.matrix[row][col] is not agent:

                        break

                    count += 1

                    if count >= WINNING_LINE:

                        return True

    return False

def full_board(board: Board) -> bool:

    return all(cell is not None for row in board.matrix for cell in row)

def apply_move(state: GameState, move: Move) -> GameState:

    new_board = state.board.copy()
    place_stone(move.placement, move.agent, new_board)
    rotate_block(new_board, move.quadrant, move.orientation)

    return GameState(new_board, OPPONENT[state.agent])    

def parse_input(state: GameState, text: str) -> Move:
    
    match = re.fullmatch(r'\s*([A-Za-z])\s*(\d)\s*([A-Za-z])\s*(\d)\s*([A-Za-z])\s*([A-Za-z])\s*', text)
    
    if match is None:
    
        raise ParseError("Input irreconhecível, tente (posição) + (quadrante) + (sentido horário ou anti-horário): [a-f][1-6] [A-B][1-2] [SH]/[AH].")
    
    placement = int(match.group(2)) - 1, ord(match.group(1).lower()) - ord('a')
    r, c = placement

    if not in_bounds((r, c)):
    
        raise BoardError(f"A dupla de coordenadas ({r + 1}, {c + 1}) não existe no tabuleiro.")
    
    if state.board.get_at(placement) is not None:
            
        raise RuleError(f"A casa nas coordenadas ({r + 1}, {c + 1}) já está ocupada.")

    quadrant = ord(match.group(3).upper()) - ord('A'), int(match.group(4)) - 1

    if not valid_quadrant(quadrant):
            
        raise BoardError("Quadrante inválido, temos linha A ou linha B + coluna 1 ou coluna 2.")

    if (match.group(5).upper() + match.group(6).upper()) == "SH":

        orientation = Orientation.CLOCKWISE

    elif (match.group(5).upper() + match.group(6).upper()) == "AH":
    
        orientation = Orientation.COUNTERCLOCK

    else:
    
        raise ParseError(f"Orientação de giro inválida, tente SH (sentido horário) ou AH (anti-horário) no final.")
    
    return Move(placement, quadrant, orientation, state.agent)

def render_row(row) -> str:

    left = " ".join(GLYPHS[cell] for cell in row[:BLOCK_SIZE])
    right = " ".join(GLYPHS[cell] for cell in row[BLOCK_SIZE:])

    return f"{left} | {right}"

def render_header() -> str:

    letters = [chr(ord("a") + col) for col in range(BOARD_SIZE)]
    left = " ".join(letters[:BLOCK_SIZE])
    right = " ".join(letters[BLOCK_SIZE:])

    return f"   {left} | {right}"

def format_board(board: Board) -> str:

    lines = [render_header()]

    for row_idx, row in enumerate(board.matrix, start=1):

        if row_idx == BLOCK_SIZE + 1:

            lines.append("   " + "-" * 13)

        lines.append(f"{row_idx:>2d} {render_row(row)}")

    return "\n".join(lines)

class Pentago(TwoPlayerGame[GameState, Move]):

    name = "Pentago"
    move_format = "[a-f][1-6] [A-B][1-2] [SH]/[AH]"

    def initial_state(self) -> GameState:

        return GameState(Board.build_initial_board(), Sides.WHITE)

    def legal_moves(self, state: GameState) -> Iterator[Move]:

        return generate_legal_moves(state)

    def parse_move(self, state: GameState, text: str) -> Move:

        return parse_input(state, text)    

    def apply_move(self, state: GameState, move: Move) -> GameState:

        return apply_move(state, move)

    def is_terminal(self, state: GameState) -> bool:

        return has_alignment(Sides.WHITE, state.board) or has_alignment(Sides.BLACK, state.board) or full_board(state.board)

    def winner(self, state: GameState) -> Sides | None:

        white = has_alignment(Sides.WHITE, state.board)
        black = has_alignment(Sides.BLACK, state.board)

        if white and not black:

            return Sides.WHITE

        elif black and not white:

            return Sides.BLACK

        else:

            return None

    def to_text(self, state: GameState) -> str:

        return format_board(state.board)

if __name__ == "__main__":

    play_in_terminal(Pentago())