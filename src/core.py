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


def create_deck() -> list[Card]:
    deck = [Card(r, s) for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck


def calculate_envido(hand: list[Card]) -> int:
    by_suit: dict[str, list[int]] = {s: [] for s in SUITS}
    for c in hand:
        by_suit[c.suit].append(c.envido_value())

    best = 0
    for vals in by_suit.values():
        if len(vals) >= 2:
            vals.sort(reverse=True)
            best = max(best, 20 + vals[0] + vals[1])
    return best if best else max(c.envido_value() for c in hand)


class GameState:
    def __init__(self, target_score: int = TARGET_SCORE):
        self.target_score = target_score
        self.player_score = 0
        self.ai_score = 0
        self.player_is_hand = True
        self.reset_round()

    def reset_round(self):
        self.deck = create_deck()
        self.player_hand = [self.deck.pop() for _ in range(3)]
        self.ai_hand = [self.deck.pop() for _ in range(3)]
        self.played_player: list[Card] = []
        self.played_ai: list[Card] = []
        self.hands_history: list[str] = []
        self.envido_available = True
        self.envido_resolved = False
        self.envido_chain: list[str] = []
        self.truco_level = 0
        self.truco_owner: str | None = None
        self.round_over = False

    def current_hand_points(self) -> int:
        return {0: 1, 1: 2, 2: 3, 3: 4}[self.truco_level]

    def next_truco_name(self) -> str:
        return {1: "truco", 2: "retruco", 3: "vale cuatro"}[self.truco_level + 1]

    def next_truco_points(self) -> int:
        return {1: 2, 2: 3, 3: 4}[self.truco_level + 1]

    def can_call_truco(self, who: str) -> bool:
            if self.truco_level >= 3:
                return False
    
            # En la primera mano solo se puede cantar truco si ya se cantó el envido
            is_first_hand = len(self.hands_history) == 0
            envido_played_or_done = bool(self.envido_chain) or self.envido_resolved
            if is_first_hand and not envido_played_or_done:
                return False
    
            if self.truco_level == 0:
                return True
    
            return self.truco_owner != who

    def award_points(self, winner: str, pts: int):
        if winner == "player":
            self.player_score += pts
        else:
            self.ai_score += pts

    def match_winner(self) -> str | None:
        if self.player_score >= self.target_score or self.ai_score >= self.target_score:
            if self.player_score == self.ai_score:
                return "player" if self.player_is_hand else "ai"
            return "player" if self.player_score > self.ai_score else "ai"
        return None

