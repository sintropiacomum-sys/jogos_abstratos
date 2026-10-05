import re
from enum import Enum
from typing import NamedTuple
from collections.abc import Iterator
from dataclasses import dataclass
from two_player_game import TwoPlayerGame, GameError, play_in_terminal

BOARD_SIZE = 19
WINNING_LINE = 5
DIRECTIONS = ((1, 1), (0, 1), (1, 0), (-1, 1))
Coord = tuple[int, int]
SQUARE_VALUES = (7, 8, 9, 10, 11)
SQUARE = frozenset((r, c) for r in SQUARE_VALUES for c in SQUARE_VALUES)

class PenteError(GameError): ...

class ParseError(PenteError): ...

class BoardError(PenteError): ...

class RuleError(PenteError): ...

class Sides(Enum):

    BLACK = "Pretas"
    WHITE = "Brancas"

SIDES = [Sides.BLACK, Sides.WHITE]
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
        initial_board[BOARD_SIZE // 2][BOARD_SIZE // 2] = Sides.WHITE
        
        return cls(initial_board)

def in_bounds(coord: Coord) -> bool:

    row, col = coord

    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

@dataclass
class GameState:

    board: Board
    agent: Sides
    scores: dict[Sides, int]
    winner: Sides | None
    plays: int

class Move (NamedTuple):

    coord: Coord
    agent: Sides

def opening_rule(plays: int, coord: Coord) -> bool:

    return plays == 2 and coord in SQUARE

def generate_legal_moves(state: GameState) -> Iterator[Move]:

    for r in range(BOARD_SIZE):

        for c in range(BOARD_SIZE):

            if state.board.get_at((r, c)) is None:

                if not opening_rule(state.plays, (r, c)):

                    yield Move((r, c), state.agent)

def parse_input(state: GameState, text: str):
    
    match = re.fullmatch(r'\s*([A-Za-z])\s*(\d{1,2})\s*', text)
    
    if match is None:
    
        raise ParseError("Input de jogada irreconhecível, tente [a-s][1-19].")
    
    row, col = int(match.group(2)) - 1, ord(match.group(1).lower()) - ord('a')

    if not in_bounds((row, col)):

        raise BoardError("Jogada fora das coordenadas do tabuleiro.")
    
    if state.board.get_at((row, col)) is not None:

        raise RuleError("Posição já ocupada.")

    if opening_rule(state.plays, (row, col)):

        raise RuleError("A segunda jogada das Brancas deve estar ao menos a 3 casas de distância do centro.")
    
    return Move((row, col), state.agent)

def place_stone(move: Move, board: Board):

    board.set_at(move.coord, move.agent)

def captures(move: Move, board: Board) -> int:

    captured_pairs = 0
    row, col = move.coord

    for dr, dc in DIRECTIONS:

        for multiplier in (1, -1):

            step_r, step_c = dr * multiplier, dc * multiplier

            r1, c1 = row + step_r * 1, col + step_c * 1
            r2, c2 = row + step_r * 2, col + step_c * 2
            r3, c3 = row + step_r * 3, col + step_c * 3

            if not in_bounds((r3, c3)):

                continue

            if (board.get_at((r1, c1)) is OPPONENT[move.agent] and
                board.get_at((r2, c2)) is OPPONENT[move.agent] and
                board.get_at((r3, c3)) is move.agent):

                board.set_at((r1, c1), None)
                board.set_at((r2, c2), None)

                captured_pairs += 1

    return captured_pairs

def check_alignment(move: Move, board: Board) -> bool:

    row, col = move.coord

    for dr, dc in DIRECTIONS:

        count = 1

        for multiplier in (1, -1):

            r, c = row + dr * multiplier, col + dc * multiplier

            while in_bounds((r, c)) and board.get_at((r, c)) is move.agent:

                count += 1
                r += dr * multiplier
                c += dc * multiplier

        if count >= WINNING_LINE:

            return True

    return False

def check_win(scores: dict[Sides, int], move: Move, board: Board) -> bool:

    return check_alignment(move, board) or scores[move.agent] >= 5

def full_board(board: Board) -> bool:

    return all(cell is not None for row in board.matrix for cell in row)

def apply_move(state: GameState, move: Move) -> GameState:

    winner = None
    new_board = state.board.copy()
    scores = state.scores.copy()
    agent = state.agent
    place_stone(move, new_board)
    captured_pairs = captures(move, new_board)
    scores[agent] += captured_pairs

    if check_win(scores, move, new_board):

        winner = move.agent

    plays = state.plays
    plays += 1

    agent = OPPONENT[agent]

    return GameState(new_board, agent, scores, winner, plays)

def render_row(row) -> str:

    return " ".join(GLYPHS[col] for col in row)

def format_board(board: Board) -> str:

    header = "   " + " ".join(chr(ord("a") + col) for col in range(BOARD_SIZE))
    
    lines = [header]

    for row_idx, row in enumerate(board.matrix, start=1):

        rendered_row = render_row(row)

        lines.append(f"{row_idx:>2d} {rendered_row}")

    return "\n".join(lines)

def format_scores(scores: dict[Sides, int]):

    printed_scores = []

    for side in SIDES:

        printed_scores.append(f"Score das {side.value}: {scores[side]}")

    return "\n".join(printed_scores)

class Pente(TwoPlayerGame[GameState, Move]):

    name = "Pente"
    move_format = "[a-s][1-19]"

    def initial_state(self) -> GameState:

        return GameState(Board.build_initial_board(), Sides.BLACK, {Sides.WHITE: 0, Sides.BLACK: 0}, None, 1)

    def legal_moves(self, state: GameState) -> Iterator[Move]:

        return generate_legal_moves(state)

    def parse_move(self, state: GameState, text: str) -> Move:

        return parse_input(state, text)    

    def apply_move(self, state: GameState, move: Move) -> GameState:

        return apply_move(state, move)

    def is_terminal(self, state: GameState) -> bool:

        return state.winner is not None or full_board(state.board)

    def winner(self, state: GameState) -> Sides | None:

        return state.winner

    def to_text(self, state: GameState) -> str:

        return format_board(state.board) + "\n\n" + format_scores(state.scores)

if __name__ == "__main__":

    play_in_terminal(Pente())