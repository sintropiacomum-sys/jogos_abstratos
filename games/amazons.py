import re
import time
import math
from enum import Enum, auto
from typing import NamedTuple
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

CLEAR = "\033[H\033[J"
BOARD_SIZE = 10
Coord = tuple[int, int]
VECTOR_VALUES: tuple[int, int, int] = (1, 0, -1)
DIRECTIONS: Iterable = tuple((dr, dc) for dr in VECTOR_VALUES for dc in VECTOR_VALUES if (dr, dc) != (0, 0))

class AmazonsError(Exception): ...

class ParseError(AmazonsError): ...

class BoardError(AmazonsError): ...

class RuleError(AmazonsError): ...

class Sides(Enum):

    BLACK = auto()
    WHITE = auto()

class Block(Enum):

    ARROW = auto()

SIDES = [Sides.BLACK, Sides.WHITE]
GLYPHS = {Sides.BLACK: "◯", Sides.WHITE: "●", Block.ARROW: "x", None: "·"}
PLAYERS = {Sides.BLACK: "Pretas", Sides.WHITE: "Brancas"}
OPPONENT = {Sides.BLACK: Sides.WHITE, Sides.WHITE: Sides.BLACK}

@dataclass
class Board:

    matrix: list[list[Sides | Block | None]]

    def get_at(self, coord: Coord) -> Sides | Block | None:
    
        r, c = coord
    
        return self.matrix[r][c]
    
    def set_at(self, coord: Coord, cell: Sides | Block | None):
    
        r, c = coord
        self.matrix[r][c] = cell

    def copy(self) -> "Board":

        new_matrix = [row.copy() for row in self.matrix]

        return Board(new_matrix)

    @classmethod
    def build_initial_board(cls) -> "Board":

        initial_board: list[list[Sides | Block | None]] = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        initial_board[3][0], initial_board[0][3], initial_board[0][6], initial_board[3][9] = Sides.WHITE, Sides.WHITE, Sides.WHITE, Sides.WHITE
        initial_board[6][0], initial_board[9][3], initial_board[9][6], initial_board[6][9] = Sides.BLACK, Sides.BLACK, Sides.BLACK, Sides.BLACK

        return cls(initial_board)

def in_bounds(cell: Coord) -> bool:

    row, col = cell

    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

def extract_direction(origin: Coord, destination: Coord):

    row_origin, col_origin = origin
    row_destination, col_destination = destination
    
    diff_row = row_destination - row_origin
    diff_col = col_destination - col_origin
    
    if diff_row == 0 and diff_col == 0:

        return (0, 0)

    gcd = math.gcd(abs(diff_row), abs(diff_col))
    
    simplified_row = diff_row // gcd
    simplified_col = diff_col // gcd
    
    return (simplified_row, simplified_col)

class Move(NamedTuple):

    origin: Coord
    destination: Coord
    arrow: Coord

@dataclass
class GameState():

    board: Board
    agent: Sides

def ray(board: Board, origin: Coord, step: Coord) -> Iterator[Coord]:

    row, col = origin
    dr, dc = step

    row, col = row + dr, col + dc

    while in_bounds((row, col)) and board.matrix[row][col] is None:

        yield row, col

        row, col = row + dr, col + dc

def legal_moves(origin: Coord, state: GameState) -> list[Move]:

    test_board = state.board.copy()
    r_origin, c_origin = origin
    test_board.matrix[r_origin][c_origin] = None
    legal_moves = []

    for step in DIRECTIONS:

        for r_destination, c_destination in ray(test_board, origin, step):

            test_board.matrix[r_destination][c_destination] = state.agent

            for step in DIRECTIONS:

                for r_arrow, c_arrow in ray(test_board, (r_destination, c_destination), step):

                    legal_moves.append(Move((r_origin, c_origin), (r_destination, c_destination), (r_arrow, c_arrow)))

            test_board.matrix[r_destination][c_destination] = None

    return legal_moves

def generate_legal_moves(state: GameState) -> Iterator[Move]:

    for r in range(BOARD_SIZE):

        for c in range(BOARD_SIZE):

            if state.board.get_at((r, c)) is state.agent:

                yield from legal_moves((r, c), state)

def apply_move(state: GameState, move: Move) -> GameState:
    
    new_board = state.board.copy()

    new_board.set_at(move.origin, None)
    new_board.set_at(move.destination, state.agent)
    new_board.set_at(move.arrow, Block.ARROW)

    return GameState(new_board, OPPONENT[state.agent])

def terminal_state(state: GameState) -> bool:

    for r in range(BOARD_SIZE):
    
            for c in range(BOARD_SIZE):
    
                if state.board.get_at((r, c)) is state.agent:

                    for step in DIRECTIONS:

                        dr, dc = step

                        if in_bounds((r + dr, c + dc)) and state.board.get_at((r + dr, c + dc)) is None:

                            return False

    return True

def ask_input(agent: Sides):

    play = str(input(f"{PLAYERS[agent]} jogam, insira origem, destino e flecha no formato [a-j][1-10] [a-j][1-10] [a-j][1-10]: "))

    return play

def parse_move(state: GameState, text: str):

    match = re.fullmatch(r'\s*([A-Za-z])\s*(\d+)\s*([A-Za-z])\s*(\d+)\s*([A-Za-z])\s*(\d+)\s*', text)

    if match is None:
        
        raise ParseError("Input irreconhecível, tente o formato origem + destino + flecha: [a-j][1-10] [a-j][1-10] [a-j][1-10].")

    origin = int(match.group(2)) - 1, ord(match.group(1).lower()) - ord('a')
    destination = int(match.group(4)) - 1, ord(match.group(3).lower()) - ord('a')
    arrow = int(match.group(6)) - 1, ord(match.group(5).lower()) - ord('a')

    r_origin, c_origin = origin
    r_destination, c_destination = destination
    r_arrow, c_arrow = arrow

    if not (in_bounds(origin) and in_bounds(destination) and in_bounds(arrow)):
        
        raise BoardError("Jogada inválida, a origem, o destino e a flecha precisam estar dentro do tabuleiro.")

    if state.board.matrix[r_origin][c_origin] is None:
                
        raise RuleError("Jogada inválida, a casa de origem está vazia.")

    if state.board.matrix[r_origin][c_origin] is not state.agent:

        raise RuleError("Jogada inválida, a peça selecionada pertence ao adversário.")

    if state.board.matrix[r_destination][c_destination] is not None:
                
        raise RuleError("Jogada inválida, a casa de destinada deve estar vazia.")

    if arrow != origin and state.board.matrix[r_arrow][c_arrow] is not None:
                    
            raise RuleError("Jogada inválida, a casa flechada deve estar vazia.")

    valid_directions = DIRECTIONS
    direction = extract_direction(origin, destination)

    if direction not in valid_directions:

        raise RuleError("Este deslocamento não é válido, movimente-se apenas ortogonalmente ou diagonalmente.")

    for move in generate_legal_moves(state):

        if origin == move.origin and destination == move.destination and arrow == move.arrow:

            return move

    else:

        raise RuleError("Jogada inválida, você deve apenas se mover e flechar mediante linhas ortogonais ou diagonais livres.")

def render_row(row) -> str:

    return " ".join(GLYPHS[col] for col in row)

def format_board(board: Board) -> str:

    header = "   " + " ".join(chr(ord("a") + col) for col in range(BOARD_SIZE))
    
    lines = [header]

    for row_idx, row in enumerate(board.matrix, start=1):

        rendered_row = render_row(row)

        lines.append(f"{row_idx:>2d} {rendered_row}")

    return "\n".join(lines)

def print_board(board: Board):

    print(format_board(board))

def play_amazons():

    state = GameState(Board.build_initial_board(), Sides.WHITE)

    while True:

        print(CLEAR, end="")
        print_board(state.board)
        print()

        if terminal_state(state):

            print(f"Estado terminal alcançado! Vencedor: {PLAYERS[OPPONENT[state.agent]]}")

            break

        try:
                
            play = ask_input(state.agent)
            move = parse_move(state, play)
            state = apply_move(state, move)

        except AmazonsError as e:
        
            print(e)
            time.sleep(2)
        
            continue

if __name__ == "__main__":

    play_amazons()