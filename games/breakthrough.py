import re
import time
from enum import Enum, auto
from typing import NamedTuple
from collections.abc import Iterator
from dataclasses import dataclass

CLEAR = "\033[H\033[J"
BOARD_SIZE = 8
Coord = tuple[int, int]
BLACK_DIAGONALS: list[Coord] = [(-1, -1), (-1, 1)]
BLACK_FORWARD: Coord = (-1, 0)
WHITE_DIAGONALS: list[Coord] = [(1, -1), (1, 1)]
WHITE_FORWARD: Coord = (1, 0)
WINNING_CAPTURES = 16

class BreakthroughError(Exception): ...

class ParseError(BreakthroughError): ...

class BoardError(BreakthroughError): ...

class RuleError(BreakthroughError): ...

class Sides(Enum):

    BLACK = auto()
    WHITE = auto()

class MoveType(Enum):

    CAPTURE = auto()
    NEUTRAL = auto()

SIDES = [Sides.BLACK, Sides.WHITE]
GLYPHS = {Sides.BLACK: "◯", Sides.WHITE: "●", None: "·"}
PLAYERS = {Sides.BLACK: "Pretas", Sides.WHITE: "Brancas"}
OPPONENT = {Sides.BLACK: Sides.WHITE, Sides.WHITE: Sides.BLACK}
MOVEMENTS = {Sides.BLACK: [*BLACK_DIAGONALS, BLACK_FORWARD],
             Sides.WHITE: [*WHITE_DIAGONALS, WHITE_FORWARD]}

@dataclass
class Board:

    matrix: list[list[Sides | None]]

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

        def make_row(piece: Sides | None) -> list[Sides | None]:

            return [piece for _ in range(BOARD_SIZE)]

        initial_board: list[list[Sides | None]] = (
            [make_row(Sides.WHITE) for _ in range(2)] +
            [make_row(None) for _ in range(BOARD_SIZE - 4)] +
            [make_row(Sides.BLACK) for _ in range(2)]
            )

        return cls(initial_board)

def in_bounds(cell: Coord) -> bool:

    row, col = cell

    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

class Move(NamedTuple):

    origin: Coord
    agent: Sides
    direction: Coord
    result: MoveType

@dataclass
class GameState():

    board: Board
    agent: Sides

def legal_move(coord: Coord, state: GameState) -> list[Move]:

    r, c = coord
    board, agent = state.board, state.agent
    legal_moves = []

    for step in MOVEMENTS[agent][0:2]:

        dr, dc = step

        if in_bounds((r + dr, c + dc)) and board.matrix[r + dr][c + dc] is not agent:

            if board.matrix[r + dr][c + dc] is OPPONENT[agent]:

                legal_moves.append(Move((r, c), agent, step, MoveType.CAPTURE))

            else:

                legal_moves.append(Move((r, c), agent, step, MoveType.NEUTRAL))

    dr, dc = MOVEMENTS[agent][2]

    if in_bounds((r + dr, c + dc)) and board.matrix[r + dr][c + dc] is None:
    
        legal_moves.append(Move((r, c), agent, (dr, dc), MoveType.NEUTRAL))

    return legal_moves

def generate_legal_moves(state: GameState) -> Iterator[Move]:

    for r in range(BOARD_SIZE):

        for c in range(BOARD_SIZE):

            if state.board.get_at((r, c)) is state.agent:

                yield from legal_move((r, c), state)

def apply_move(state: GameState, move: Move) -> GameState:

    destination = (move.origin[0] + move.direction[0],
                   move.origin[1] + move.direction[1])
    
    new_board = state.board.copy()

    new_board.set_at(move.origin, None)
    new_board.set_at(destination, move.agent)

    return GameState(new_board, OPPONENT[move.agent])

def reached_other_side(board: Board, side: Sides) -> bool:

    target_row = BOARD_SIZE - 1 if side is Sides.WHITE else 0

    return any(board.get_at((target_row, c)) is side for c in range(BOARD_SIZE))

def captured_all(board: Board, side: Sides) -> bool:

    opponent = OPPONENT[side]

    return not any(
        board.get_at((r, c)) is opponent
        for r in range(BOARD_SIZE)
        for c in range(BOARD_SIZE)
    )

def get_winner(board: Board) -> Sides | None:

    for side in SIDES:

        if reached_other_side(board, side) or captured_all(board, side):

            return side

    return None

def ask_input(agent: Sides):

    play = str(input(f"{PLAYERS[agent]} jogam, insira [a-h][1-8] [a-h][1-8]: "))

    return play

def parse_move(state: GameState, text: str):

    match = re.fullmatch(r'\s*([A-Za-z])\s*(\d)\s*([A-Za-z])\s*(\d)\s*', text)

    if match is None:
        
        raise ParseError("Input irreconhecível, tente (origem) + (destino): [a-h][1-8] [a-h][1-8].")

    origin = int(match.group(2)) - 1, ord(match.group(1).lower()) - ord('a')
    destination = int(match.group(4)) - 1, ord(match.group(3).lower()) - ord('a')

    r_origin, c_origin = origin
    r_destination, c_destination = destination

    if not (in_bounds(origin) and in_bounds(destination)):
        
        raise BoardError("Jogada inválida, tanto a origem quanto o destino precisam estar dentro do tabuleiro.")

    if state.board.matrix[r_origin][c_origin] is None:
                
        raise RuleError("Jogada inválida, a casa de origem está vazia.")

    if state.board.matrix[r_origin][c_origin] is not state.agent:

        raise RuleError("Jogada inválida, a peça selecionada pertence ao adversário.")

    valid_directions = MOVEMENTS[state.agent]
    direction = (r_destination - r_origin, c_destination - c_origin)

    if direction not in valid_directions:

        raise RuleError("Este deslocamento não é válido, tente avançar apenas uma casa para frente ou para as diagonais")

    for move in generate_legal_moves(state):

        if origin == move.origin and direction == move.direction:

            return move

    else:

        raise RuleError("Jogada inválida, capturas de peças opostas só podem ocorrer na diagonal, em todos os outros casos o destino deve estar vazio.")

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

def play_breakthrough():

    state = GameState(Board.build_initial_board(), Sides.WHITE)

    while True:

        print(CLEAR, end="")
        print_board(state.board)
        print()

        winner = get_winner(state.board)

        if winner is not None:

            print(f"Estado terminal alcançado! Vencedor: {PLAYERS[winner]}")

            break

        try:

            play = ask_input(state.agent)
            move = parse_move(state, play)
            state = apply_move(state, move)

        except BreakthroughError as e:

            print(e)
            time.sleep(2)

if __name__ == "__main__":

    play_breakthrough()      