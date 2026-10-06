import re
from enum import Enum
from typing import NamedTuple
from collections.abc import Iterator
from dataclasses import dataclass
from two_player_game import TwoPlayerGame, GameError, play_in_terminal

SIZE = 8
DIRECTIONS = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0))
Coord = tuple[int, int]

class OthelloError(GameError): ...

class ParseError(OthelloError): ...

class BoardError(OthelloError): ...

class RuleError(OthelloError): ...

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

        initial_board: list[list[Sides | None]] = [[None for _ in range(SIZE)] for _ in range(SIZE)]
        initial_board[3][3], initial_board[4][4] = Sides.WHITE, Sides.WHITE
        initial_board[4][3], initial_board[3][4] = Sides.BLACK, Sides.BLACK
        
        return cls(initial_board)

def in_bounds(coord: Coord) -> bool:

    row, col = coord

    return 0 <= row < SIZE and 0 <= col < SIZE

def ray(origin: Coord, step: Coord) -> Iterator[Coord]:

    row, col = origin
    dr, dc = step
    row, col = row + dr, col + dc

    while in_bounds((row, col)):

        yield row, col

        row, col = row + dr, col + dc

@dataclass
class GameState:

    board: Board
    agent: Sides
    passed: Sides | None

class Move (NamedTuple):

    origin: Coord
    agent: Sides

def flips(move: Move, board: Board) -> tuple[Coord, ...]:

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

def is_legal(move: Move, board: Board) -> bool:

    if not in_bounds(move.origin):

        return False
        
    r, c = move.origin

    return board.matrix[r][c] is None and bool(flips(move, board))

def generate_legal_moves(agent: Sides, board: Board) -> Iterator[Move]:

    for r in range(SIZE):

        for c in range(SIZE):

            move = Move((r, c), agent)

            if is_legal(move, board):

                yield move

def parse_input(state: GameState, text: str) -> Move:
    
    match = re.fullmatch(r'\s*([A-Za-z])\s*(\d)\s*', text)
    
    if match is None:
    
        raise ParseError("Input de jogada irreconhecível, tente [a-h][1-8].")
    
    r, c = int(match.group(2)) - 1, ord(match.group(1).upper()) - ord('A')

    if not in_bounds((r, c)):
    
        raise BoardError(f"A dupla de coordenadas ({r + 1}, {c + 1}) não existe no tabuleiro.")

    if state.board.get_at((r, c)) is not None:
        
        raise RuleError(f"A casa nas coordenadas ({r + 1}, {c + 1}) já está ocupada.")

    move = Move((r, c), state.agent)

    if not flips(move, state.board):

        raise RuleError(f"A jogada em ({r + 1}, {c + 1}) não flanqueia peças adversárias.")
    
    return move

def has_legal_moves(agent: Sides, board: Board) -> bool:

    return any(True for _ in generate_legal_moves(agent, board))

def apply_move(state: GameState, move: Move) -> GameState:

    new_board = state.board.copy()
    agent = move.agent
    r, c = move.origin
    passed = None

    new_board.set_at((r, c), agent)
    flipped_pieces = flips(move, new_board)

    for f_r, f_c in flipped_pieces:

        new_board.set_at((f_r, f_c), agent)

    if has_legal_moves(OPPONENT[agent], new_board):

        agent = OPPONENT[agent]
        passed = None

    elif has_legal_moves(agent, new_board):

        passed = OPPONENT[agent]

    return GameState(new_board, agent, passed)

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

def render_row(row) -> str:

    return " ".join(GLYPHS[col] for col in row)

def format_board(board: Board) -> str:

    header = "   " + " ".join(chr(ord("a") + col) for col in range(SIZE))
    
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

class Othello(TwoPlayerGame[GameState, Move]):

    name = "Othello"
    move_format = "[a-h][1-8]"

    def initial_state(self) -> GameState:

        return GameState(Board.build_initial_board(), Sides.BLACK, None)

    def legal_moves(self, state: GameState) -> Iterator[Move]:

        return generate_legal_moves(state.agent, state.board)

    def parse_move(self, state: GameState, text: str) -> Move:

        return parse_input(state, text)    

    def apply_move(self, state: GameState, move: Move) -> GameState:

        return apply_move(state, move)

    def is_terminal(self, state: GameState) -> bool:

        return game_over(state.board)

    def winner(self, state: GameState) -> Sides | None:

        return game_result(state.board)

    def to_text(self, state: GameState) -> str:

        text = format_board(state.board) + "\n\n" + format_scores(count_scores(state.board))

        if state.passed is not None:
             
            return text + "\n\n" + f"Sem jogadas, as {state.passed.value} passaram."

        else:

            return text

if __name__ == "__main__":

    play_in_terminal(Othello())