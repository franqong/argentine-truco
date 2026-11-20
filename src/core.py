import random

SUITS = ("Spades", "Clubs", "Gold", "Cups")
RANKS = (1, 2, 3, 4, 5, 6, 7, 10, 11, 12)
TARGET_SCORE = 15


class Card:
    def __init__(self, rank: int, suit: str):
        self.rank = rank
        self.suit = suit

    def __str__(self) -> str:
        return f"{self.rank} of {self.suit}"

    def card_power(self) -> int:
        if self.rank == 1 and self.suit == "Spades":
            return 14
        if self.rank == 1 and self.suit == "Clubs":
            return 13
        if self.rank == 7 and self.suit == "Spades":
            return 12
        if self.rank == 7 and self.suit == "Gold":
            return 11
        if self.rank == 3:
            return 10
        if self.rank == 2:
            return 9
        if self.rank == 1:
            return 8
        if self.rank in (12, 11, 10):
            return {12: 7, 11: 6, 10: 5}[self.rank]
        if self.rank == 7:
            return 4
        return {6: 3, 5: 2, 4: 1}[self.rank]

    def envido_value(self) -> int:
        return 0 if self.rank in (10, 11, 12) else self.rank