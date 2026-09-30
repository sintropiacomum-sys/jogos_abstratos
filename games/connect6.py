from dataclasses import dataclass
import re
from enum import Enum
from typing import NamedTuple
from collections.abc import Iterator
from two_player_game import TwoPlayerGame, GameError, play_in_terminal

BOARD_SIZE = 19
WINNING_LINE = 6
DIRECTIONS = ((1, 1), (0, 1), (1, 0), (-1, 1))
Coord = tuple[int, int]

class Connect6Error(GameError): ...

class ParseError(Connect6Error): ...

class BoardError(Connect6Error): ...

class RuleError(Connect6Error): ...

class Sides(Enum):

    BLACK = "Pretas"
    WHITE = "Brancas"

GLYPHS = {Sides.BLACK: "◯", Sides.WHITE: "●", None: "·"}
OPPONENT = {Sides.BLACK: Sides.WHITE, Sides.WHITE: Sides.BLACK}

def in_bounds(row, col) -> bool:

    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

@dataclass
class Board:

    matrix: list[list[None | Sides]]

    def get_at(self, coord: Coord) -> Sides | None:
        
        r, c = coord
    
        return self.matrix[r][c]
        
    def set_at(self, coord: Coord, cell: Sides):
    
        r, c = coord
        self.matrix[r][c] = cell

    def copy(self) -> "Board":
    
        new_matrix = [row.copy() for row in self.matrix]

        return Board(new_matrix)

    @classmethod
    def build_initial_board(cls) -> "Board":

        initial_board: list[list[Sides | None]] = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        
        return cls(initial_board)

@dataclass
class GameState:

    board: Board
    agent: Sides
    plays: int
    winner: Sides | None

class Move (NamedTuple):

    coord: Coord
    agent: Sides

def generate_legal_moves(state: GameState) -> Iterator[Move]:

    for r in range(BOARD_SIZE):

        for c in range(BOARD_SIZE):

            if state.board.get_at((r, c)) is None:

                yield Move((r, c), state.agent)

def parse_input(state: GameState, text: str) -> Move:
    
    match = re.fullmatch(r'\s*([A-Za-z])\s*(\d{1,2})\s*', text)
    
    if match is None:
    
        raise ParseError("Input de jogada irreconhecível, tente [a-s][1-19].")
    
    row, col = int(match.group(2)) - 1, ord(match.group(1).upper()) - ord('A')

    if not in_bounds(row, col):
    
        raise BoardError("Jogada fora das coordenadas do tabuleiro.")
        
    if state.board.get_at((row, col)) is not None:

        raise RuleError("Posição já ocupada.")
    
    return Move((row, col), state.agent)

def place_stone(board: Board, move: Move):

    board.set_at(move.coord, move.agent)

def check_alignment(move: Move, board: Board) -> bool:

    row, col = move.coord

    for dr, dc in DIRECTIONS:

        count = 1

        for multiplier in (1, -1):

            r, c = row + dr * multiplier, col + dc * multiplier

            while in_bounds(r, c) and board.matrix[r][c] is move.agent:

                count += 1
                r += dr * multiplier
                c += dc * multiplier

        if count >= WINNING_LINE:

            return True

    return False

def full_board(plays: int) -> bool:

    return plays >= (BOARD_SIZE ** 2)

def apply_move(state: GameState, move: Move):

    winner = None
    new_board = state.board.copy()
    agent = state.agent
    place_stone(new_board, move)
    plays = state.plays
    plays += 1
    
    if check_alignment(move, new_board):

        winner = move.agent

    elif plays % 2 == 1:

        agent = OPPONENT[agent]

    return GameState(new_board, agent, plays, winner)

def render_row(row) -> str:
    
    return " ".join(GLYPHS[col] for col in row)

def format_board(board: Board) -> str:

    header = "   " + " ".join(chr(ord("a") + col) for col in range(BOARD_SIZE))
    
    lines = [header]

    for row_idx, row in enumerate(board.matrix, start=1):

        rendered_row = render_row(row)

        lines.append(f"{row_idx:>2d} {rendered_row}")

    return "\n".join(lines)

class Connect6(TwoPlayerGame[GameState, Move]):

    name = "Connect6"
    move_format = "[a-s][1-19]"

    def initial_state(self) -> GameState:

        return GameState(Board.build_initial_board(), Sides.BLACK, 0, None)

    def legal_moves(self, state: GameState) -> Iterator[Move]:

        return generate_legal_moves(state)

    def parse_move(self, state: GameState, text: str) -> Move:

        return parse_input(state, text)    

    def apply_move(self, state: GameState, move: Move) -> GameState:

        return apply_move(state, move)

    def is_terminal(self, state: GameState) -> bool:

        return state.winner is not None or full_board(state.plays)

    def winner(self, state: GameState) -> Sides | None:

        return state.winner

    def to_text(self, state: GameState) -> str:

        return format_board(state.board)

if __name__ == "__main__":

    play_in_terminal(Connect6())