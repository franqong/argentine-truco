import tkinter as tk
from tkinter import messagebox

from src.core import (
    Card,
    GameState,
    ai_envido_action,
    ai_pick_card,
    ai_truco_action,
    calculate_envido,
    compute_envido_stakes,
    get_envido_raises,
    is_round_over,
    resolve_envido,
    resolve_hand,
    round_winner,
)

SUIT_COLOR = {"Spades": "#1e3a8a", "Clubs": "#166534", "Gold": "#b45309", "Cups": "#b91c1c"}
FIG_NAME = {10: "Sota", 11: "Caballo", 12: "Rey"}


class MinimalTrucoGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Argentine Truco: A Card Game")
        self.root.geometry("820x520")
        self.root.resizable(False, False)

        self.state = GameState()
        self.msg = ""
        self.awaiting: str | None = None
        self.p_card: Card | None = None
        self.a_card: Card | None = None
        self.turn_player = True
        self.lead_player = True
        self.rules_win: tk.Toplevel | None = None

        self.hud = tk.Label(root, text="", font=("Sans", 11, "bold"), pady=6)
        self.hud.pack()

        self.canvas = tk.Canvas(root, width=820, height=380, bg="#1d4e3e", highlightthickness=0)
        self.canvas.pack()

        bar = tk.Frame(root, pady=6)
        bar.pack()

        self.b_env = tk.Button(bar, text="Envido", command=lambda: self.call_envido("envido"))
        self.b_real = tk.Button(bar, text="Real Envido", command=lambda: self.call_envido("real envido"))
        self.b_falta = tk.Button(bar, text="Falta Envido", command=lambda: self.call_envido("falta envido"))
        self.b_truco = tk.Button(bar, text="Truco", command=self.call_truco)
        self.b_fold = tk.Button(bar, text="Fold", command=self.fold)
        self.b_rules = tk.Button(bar, text="Rules", command=self.show_rules)
        self.b_new = tk.Button(bar, text="Reset", command=self.new_match)

        for b in (
            self.b_env,
            self.b_real,
            self.b_falta,
            self.b_truco,
            self.b_fold,
            self.b_rules,
            self.b_new,
        ):
            b.pack(side=tk.LEFT, padx=4)

        self.resp_bar = tk.Frame(root)
        self.resp_bar.pack(pady=2)

    def _draw_suit(self, cx: float, cy: float, suit: str, s: float = 1.0, tag: str = ""):
            col = SUIT_COLOR[suit]
            if suit == "Gold":
                r1, r2 = 12 * s, 6 * s
                self.canvas.create_oval(cx - r1, cy - r1, cx + r1, cy + r1, fill="#f59e0b", outline=col, width=2, tags=tag)
                self.canvas.create_oval(cx - r2, cy - r2, cx + r2, cy + r2, fill="#fffdf8", outline=col, width=1, tags=tag)
            elif suit == "Cups":
                self.canvas.create_arc(
                    cx - 11 * s, cy - 13 * s, cx + 11 * s, cy + 3 * s,
                    start=180, extent=180, fill=col, outline=col, tags=tag
                )
                self.canvas.create_line(cx, cy + 3 * s, cx, cy + 11 * s, fill=col, width=max(1, int(2.5 * s)), tags=tag)
                self.canvas.create_line(cx - 8 * s, cy + 11 * s, cx + 8 * s, cy + 11 * s, fill=col, width=max(1, int(2.5 * s)), tags=tag)
            elif suit == "Spades":
                # Espada en diagonal (/)
                self.canvas.create_line(
                    cx - 10 * s, cy + 10 * s, cx + 8 * s, cy - 8 * s,
                    fill=col, width=max(2, int(3.5 * s)), tags=tag
                )
                self.canvas.create_polygon(
                    cx + 12 * s, cy - 12 * s,
                    cx + 4 * s, cy - 8 * s,
                    cx + 8 * s, cy - 4 * s,
                    fill=col, outline=col, tags=tag
                )
                self.canvas.create_line(
                    cx - 4 * s, cy - 2 * s, cx + 4 * s, cy + 6 * s,
                    fill=col, width=max(1, int(2.5 * s)), tags=tag
                )
                self.canvas.create_line(
                    cx, cy + 2 * s, cx - 12 * s, cy + 14 * s,
                    fill="#3b82f6", width=max(1, int(2.5 * s)), tags=tag
                )
            else:  # Clubs (Basto)
                self.canvas.create_line(
                    cx - 9 * s, cy - 9 * s, cx + 9 * s, cy + 9 * s,
                    fill=col, width=max(2, int(4 * s)), tags=tag
                )
                self.canvas.create_oval(
                    cx - 12 * s, cy - 12 * s, cx - 4 * s, cy - 4 * s,
                    fill="#22c55e", outline=col, width=1.5, tags=tag
                )
                self.canvas.create_oval(
                    cx + 4 * s, cy + 4 * s, cx + 12 * s, cy + 12 * s,
                    fill="#22c55e", outline=col, width=1.5, tags=tag
                )

    def _card(self, x: int, y: int, card: Card, tag: str, active: bool):
            col = SUIT_COLOR[card.suit]
            self.canvas.create_rectangle(
                x, y, x + 75, y + 95,
                fill="#fffdf8", outline="#facc15" if active else "#222",
                width=2 if active else 1, tags=tag
            )
            self.canvas.create_text(x + 16, y + 15, text=str(card.rank), fill=col, font=("Sans", 11, "bold"), tags=tag)
            self._draw_suit(x + 56, y + 16, card.suit, s=0.55, tag=tag)
            self._draw_suit(x + 37, y + 48, card.suit, s=1.05, tag=tag)
            label = FIG_NAME.get(card.rank, f"Env {card.envido_value()}")
            self.canvas.create_text(x + 37, y + 81, text=label, fill="#555", font=("Sans", 8), tags=tag)
    
        def _mini_card(self, x: int, y: int, card: Card):
            col = SUIT_COLOR[card.suit]
            self.canvas.create_rectangle(x, y, x + 75, y + 50, fill="#fffdf8", outline="#222")
            self.canvas.create_text(x + 24, y + 25, text=str(card.rank), fill=col, font=("Sans", 10, "bold"))
            self._draw_suit(x + 50, y + 25, card.suit, s=0.65)

    def new_match(self):
            self.state = GameState()
            self.start_round()
    
    def start_round(self):
        if self.state.match_winner():
            self.end_match()
            return
        self.state.reset_round()
        self.p_card = None
        self.a_card = None
        self.awaiting = None
        self.turn_player = self.state.player_is_hand
        self.lead_player = self.turn_player
        self.msg = "New round — " + ("Your lead" if self.turn_player else "AI lead")
        self.render()
        if not self.turn_player:
            self.root.after(500, self.ai_step)

    def end_match(self):
        w = self.state.match_winner()
        res = f"You win ({self.state.player_score}-{self.state.ai_score})" if w == "player" else f"AI wins ({self.state.ai_score}-{self.state.player_score})"
        if messagebox.askyesno("Match Over", f"{res}\nPlay again?"):
            self.new_match()


def main():
    root = tk.Tk()
    MinimalTrucoGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()