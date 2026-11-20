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


def main():
    root = tk.Tk()
    MinimalTrucoGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()