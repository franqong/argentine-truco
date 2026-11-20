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


def compute_envido_stakes(chain: list[str], state: GameState) -> tuple[int, int]:
    refused = min(len(chain), 3)
    if chain == ["envido", "envido"]:
        accepted = 4
    else:
        last = chain[-1]
        if last == "envido":
            accepted = 2
        elif last == "real envido":
            accepted = 3
        else:  # falta envido
            accepted = max(1, state.target_score - max(state.player_score, state.ai_score))
    return accepted, refused


def get_envido_raises(chain: list[str]) -> list[str]:
    if len(chain) >= 3:
        return []
    out = []
    if len(chain) == 1 and chain[-1] == "envido":
        out.append("envido")
    if "real envido" not in chain:
        out.append("real envido")
    if "falta envido" not in chain:
        out.append("falta envido")
    return out


def resolve_envido(state: GameState) -> tuple[str, int, int]:
    p, a = calculate_envido(state.player_hand), calculate_envido(state.ai_hand)
    if p > a:
        return "player", p, a
    if a > p:
        return "ai", p, a
    return ("player" if state.player_is_hand else "ai"), p, a


def resolve_hand(p_card: Card, a_card: Card) -> str:
    if p_card.card_power() > a_card.card_power():
        return "player"
    if a_card.card_power() > p_card.card_power():
        return "ai"
    return "tie"


def is_round_over(state: GameState) -> bool:
    h = state.hands_history
    p_w, a_w = h.count("player"), h.count("ai")

    # Alguien llegó a 2 manos ganadas
    if p_w == 2 or a_w == 2:
        return True

    # Se jugaron las 3 manos
    if len(h) == 3:
        return True

    # 1ra parda y 2da ganada por X: la ronda ya se define a favor de X
    if len(h) == 2 and h[0] == "tie" and h[1] in ("player", "ai"):
        return True

    # 1ra ganada por X y 2da parda: la ronda se define a favor de X sin jugar 3ra
    if len(h) == 2 and h[1] == "tie" and h[0] in ("player", "ai"):
        return True

    return False


def round_winner(state: GameState) -> str:
    h = state.hands_history
    p_w, a_w = h.count("player"), h.count("ai")
    mano = "player" if state.player_is_hand else "ai"

    # Quien llegó a 2 manos ganadas
    if p_w == 2:
        return "player"
    if a_w == 2:
        return "ai"

    # Si hubo parda en la 1ra mano, define la 2da; si también se parda, define la 3ra
    if len(h) >= 1 and h[0] == "tie":
        if len(h) >= 2 and h[1] in ("player", "ai"):
            return h[1]
        if len(h) >= 3 and h[2] in ("player", "ai"):
            return h[2]
        return mano

    # Si se ganó en la 1ra y se pardó en la 2da, gana quien ganó la 1ra
    if len(h) >= 2 and h[1] == "tie" and h[0] in ("player", "ai"):
        return h[0]

    # Si se llega a la 3ra con 1 mano cada uno y se parda en la 3ra, gana el mano
    if len(h) == 3 and h[2] == "tie":
        return mano

    if p_w != a_w:
        return "player" if p_w > a_w else "ai"

    return mano


def ai_envido_action(state: GameState) -> str:
    ev = calculate_envido(state.ai_hand)
    if len(state.envido_chain) < 3 and ev >= 29 and "falta envido" not in state.envido_chain:
        return "falta envido"
    if len(state.envido_chain) == 1 and ev >= 25 and "real envido" not in state.envido_chain:
        return "real envido"
    if len(state.envido_chain) == 1 and state.envido_chain[-1] == "envido" and ev >= 23:
        return "envido"
    return "quiero" if ev >= 21 else "no quiero"


def ai_truco_action(state: GameState) -> str:
    strength = sum(c.card_power() for c in state.ai_hand)
    if strength >= 30 and state.truco_level + 1 < 3:
        return "raise"
    if strength >= 18 or (state.truco_level == 0 and strength >= 13):
        return "quiero"
    return "no quiero"


def ai_pick_card(hand: list[Card], lead_card: Card | None) -> Card:
    ordered = sorted(hand, key=lambda c: c.card_power())
    if lead_card is None:
        return ordered[0]
    winners = [c for c in ordered if c.card_power() >= lead_card.card_power()]
    return winners[0] if winners else ordered[0]