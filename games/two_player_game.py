import html
from abc import ABC, abstractmethod
from collections.abc import Iterable
from enum import Enum
from typing import Protocol

CLEAR = "\033[H\033[J"

class GameError(Exception): ...

class AbstractGameState(Protocol):

    @property
    def agent(self) -> Enum:

        ...

class TwoPlayerGame[State: AbstractGameState, Move](ABC):

    name: str
    move_format: str

    def __init__(self) -> None:

        self.game_state: State = self.initial_state()
        self.move_history: list[Move] = []

    @abstractmethod
    def initial_state(self) -> State:

        ...

    @abstractmethod
    def legal_moves(self, state: State) -> Iterable[Move]:

        ...

    @abstractmethod
    def parse_move(self, state: State, text: str) -> Move:

        ...

    @abstractmethod
    def apply_move(self, state: State, move: Move) -> State:

        ...

    @abstractmethod
    def is_terminal(self, state: State) -> bool:

        ...

    @abstractmethod
    def winner(self, state: State) -> Enum | None:

        ...

    @abstractmethod
    def to_text(self, state: State) -> str:

        ...

    def to_html(self, state: State) -> str:

        return f"<pre>{html.escape(self.to_text(state))}</pre>"

    def play(self, move: Move) -> None:

        self.game_state = self.apply_move(self.game_state, move)
        self.move_history.append(move)

def play_in_terminal[State: AbstractGameState, Move](game: TwoPlayerGame[State, Move]) -> None:

    message = ""

    while not game.is_terminal(game.game_state):

        print(CLEAR, end="")
        print(game.to_text(game.game_state))
        print(message)

        try:

            text = input(f"{game.game_state.agent.value} jogam, insira {game.move_format}: ")
            move = game.parse_move(game.game_state, text)
            game.play(move)
            message = ""

        except GameError as error:

            message = str(error)

    winner = game.winner(game.game_state)

    print(CLEAR, end="")
    print(game.to_text(game.game_state))
    print()

    if winner is None:

        print("O resultado é um empate.")

    else:

        print(f"Vencedor: {winner.value}.")