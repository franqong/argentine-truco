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

        self.new_match()

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

    def can_act(self) -> bool:
        return not self.state.round_over and self.turn_player and self.awaiting is None and self.p_card is None

    def play_card(self, idx: int):
        if not self.can_act() or idx >= len(self.state.player_hand):
            return
        self.p_card = self.state.player_hand.pop(idx)
        self.state.played_player.append(self.p_card)
        self.state.envido_available = False
        self.turn_player = False
        self.msg = f"You played {self.p_card}"
        self.render()
        self.root.after(500, self.finish_hand if self.a_card else self.ai_step)

    def ai_step(self):
        if self.state.round_over or self.turn_player or self.awaiting:
            return
        if self.state.envido_available and not self.state.envido_resolved and not self.state.played_ai:
            if calculate_envido(self.state.ai_hand) >= 24:
                call = "real envido" if calculate_envido(self.state.ai_hand) >= 27 else "envido"
                self.state.envido_chain = [call]
                self.awaiting = "envido"
                acc, ref = compute_envido_stakes(self.state.envido_chain, self.state)
                self.msg = f"AI calls {call.upper()} (Want: {acc} | Pass: {ref})"
                self.render()
                return
        if (
            self.state.truco_level == 0
            and self.state.can_call_truco("ai")
            and sum(c.card_power() for c in self.state.ai_hand) >= 24
        ):
            self.awaiting = "truco"
            self.msg = f"AI calls TRUCO (Want: {self.state.next_truco_points()} | Pass: {self.state.current_hand_points()})"
            self.render()
            return

        lead = self.p_card if self.lead_player else None
        self.a_card = ai_pick_card(self.state.ai_hand, lead)
        self.state.ai_hand.remove(self.a_card)
        self.state.played_ai.append(self.a_card)
        self.state.envido_available = False
        self.turn_player = True
        self.msg = f"AI played {self.a_card}"
        self.render()
        if self.p_card:
            self.root.after(500, self.finish_hand)

    def finish_hand(self):
        if not self.p_card or not self.a_card:
            return
        w = resolve_hand(self.p_card, self.a_card)
        self.state.hands_history.append(w)
        self.turn_player = True if w == "player" else (False if w == "ai" else self.lead_player)
        self.lead_player = self.turn_player
        self.p_card = None
        self.a_card = None
        self.msg = {"player": "You won hand", "ai": "AI won hand", "tie": "Parda (Hand tied)"}[w]
        self.render()

        if is_round_over(self.state):
            self.root.after(700, self.finish_round)
        elif not self.turn_player:
            self.root.after(500, self.ai_step)

    def finish_round(self):
        if not self.state.round_over:
            w = round_winner(self.state)
            pts = self.state.current_hand_points()
            self.state.award_points(w, pts)
            self.state.round_over = True
            self.msg = f"{'You' if w == 'player' else 'AI'} won round (+{pts})"
            self.render()
        self.state.player_is_hand = not self.state.player_is_hand
        self.root.after(900, self.end_match if self.state.match_winner() else self.start_round)

    def end_match(self):
        w = self.state.match_winner()
        res = f"You win ({self.state.player_score}-{self.state.ai_score})" if w == "player" else f"AI wins ({self.state.ai_score}-{self.state.player_score})"
        if messagebox.askyesno("Match Over", f"{res}\nPlay again?"):
            self.new_match()

    def fold(self):
        if self.state.round_over:
            return
        pts = self.state.current_hand_points()
        self.state.award_points("ai", pts)
        self.state.round_over = True
        self.awaiting = None
        self.msg = f"Folded — AI +{pts}"
        self.render()
        self.state.player_is_hand = not self.state.player_is_hand
        self.root.after(800, self.start_round)

    def call_envido(self, call: str):
        # El jugador puede cantar envido antes de tirar su primera carta, incluso siendo pie
        if not self.can_act() or self.state.envido_resolved or self.state.played_player:
            return
        self.state.envido_chain = [call]
        self._ai_react_envido()

    def _ai_react_envido(self):
        acc, ref = compute_envido_stakes(self.state.envido_chain, self.state)
        act = ai_envido_action(self.state)
        if act == "no quiero":
            self.state.award_points("player", ref)
            self.state.envido_resolved = True
            self.state.envido_available = False
            self.msg = f"AI passed Envido — You +{ref}"
            self.render()
        elif act == "quiero":
            self._settle_envido(acc)
        else:
            self.state.envido_chain.append(act)
            self.awaiting = "envido"
            a2, r2 = compute_envido_stakes(self.state.envido_chain, self.state)
            self.msg = f"AI raised {act.upper()} (Want: {a2} | Pass: {r2})"
            self.render()

    def _settle_envido(self, pts: int):
        w, p, a = resolve_envido(self.state)
        self.state.award_points(w, pts)
        self.state.envido_resolved = True
        self.state.envido_available = False
        self.awaiting = None
        self.msg = f"Envido You {p} vs AI {a} -> {'You' if w == 'player' else 'AI'} +{pts}"
        self.render()
        if self.state.match_winner():
            self.root.after(700, self.end_match)
        elif not self.turn_player:
            self.root.after(500, self.ai_step)

    def resp_envido(self, choice: str):
        if self.awaiting != "envido":
            return
        acc, ref = compute_envido_stakes(self.state.envido_chain, self.state)
        if choice == "no quiero":
            self.state.award_points("ai", ref)
            self.state.envido_resolved = True
            self.state.envido_available = False
            self.awaiting = None
            self.msg = f"Passed Envido — AI +{ref}"
            self.render()
            if not self.turn_player:
                self.root.after(500, self.ai_step)
        elif choice == "quiero":
            self._settle_envido(acc)
        else:
            self.state.envido_chain.append(choice)
            self.awaiting = None
            self._ai_react_envido()

    def call_truco(self):
        if not self.can_act() or not self.state.can_call_truco("player"):
            return
        self._ai_react_truco()

    def _ai_react_truco(self):
        name = self.state.next_truco_name()
        ref = self.state.current_hand_points()
        act = ai_truco_action(self.state)
        if act == "no quiero":
            self.state.award_points("player", ref)
            self.state.round_over = True
            self.msg = f"AI passed {name.upper()} — You +{ref}"
            self.render()
            self.state.player_is_hand = not self.state.player_is_hand
            self.root.after(800, self.start_round)
        elif act == "raise":
            # El jugador cantó el escalón actual y la IA lo acepta y sube al siguiente
            self.state.truco_level += 2
            self.state.truco_owner = "ai"
            self.awaiting = "truco"
            self.msg = f"AI raised {self.state.next_truco_name().upper()} ({self.state.next_truco_points()} pts)"
            self.render()
        else:
            # La IA acepta el canto del jugador; el jugador sigue siendo quien lo cantó
            self.state.truco_level += 1
            self.state.truco_owner = "player"
            self.msg = f"AI wanted — Round worth {self.state.current_hand_points()} pts"
            self.render()

    def resp_truco(self, choice: str):
        if self.awaiting != "truco":
            return
        ref = self.state.current_hand_points()
        if choice == "no quiero":
            self.state.award_points("ai", ref)
            self.state.round_over = True
            self.awaiting = None
            self.msg = f"Passed — AI +{ref}"
            self.render()
            self.state.player_is_hand = not self.state.player_is_hand
            self.root.after(800, self.start_round)
        elif choice == "quiero":
            # El jugador acepta el canto de la IA; la IA mantiene truco_owner para que el jugador pueda subir luego
            self.state.truco_level += 1
            self.state.truco_owner = "ai"
            self.awaiting = None
            self.msg = f"Wanted — Round worth {self.state.current_hand_points()} pts"
            self.render()
            if not self.turn_player:
                self.root.after(500, self.ai_step)
        else:
            # El jugador acepta el canto de la IA y sube al siguiente escalón
            self.state.truco_level += 1
            self.state.truco_owner = "player"
            self.awaiting = None
            self._ai_react_truco()

    def show_rules(self):
        if self.rules_win and self.rules_win.winfo_exists():
            self.rules_win.lift()
            return

        win = tk.Toplevel(self.root)
        win.title("Rules — Argentine Truco")
        win.geometry("540x480")
        win.resizable(False, False)
        win.configure(bg="#111827")
        self.rules_win = win

        tk.Label(
            win,
            text="ARGENTINE TRUCO (15-Point Match)",
            fg="#fef08a",
            bg="#111827",
            font=("Sans", 13, "bold"),
            pady=10,
        ).pack()

        sections = [
            (
                "Spanish 40-Card Deck",
                "• Ranks: 1–7 and face cards 10 (Sota), 11 (Caballo), 12 (Rey).\n"
                "• Suits: Spades (blue sword), Clubs (green), Gold (coin), Cups (red).",
            ),
            (
                "Card Hierarchy (Highest to Lowest)",
                "1 Spades > 1 Clubs > 7 Spades > 7 Gold > 3s > 2s >\n"
                "1 Gold / 1 Cups > 12 > 11 > 10 > 7 Cups / 7 Clubs > 6 > 5 > 4.",
            ),
            (
                "Hands & Pardas (Ties)",
                "• Best of 3 hands wins the round. 'Mano' is the player who starts.\n"
                "• Hand 1 parda: Hand 2 decides (or Hand 3 if tied again).\n"
                "• Win Hand 1 + Hand 2 parda: Hand 1 winner takes the round.\n"
                "• Hand 3 parda: 'Mano' wins the round.",
            ),
            (
                "Envido (Before Playing Your First Card)",
                "• 20 + two same-suit cards (10/11/12 = 0), or highest single card.\n"
                "• Envido-Envido = 4 pts (2 pts if refused).\n"
                "• Refused ('No quiero'): 1 pt (direct), 2 pts (2nd step), 3 pts (3rd step).",
            ),
            (
                "Truco Ladder",
                "• Cannot call Truco in Hand 1 without calling Envido first.\n"
                "• No call = 1 pt   |   Truco = 2 pts   |   Retruco = 3 pts   |   Vale Cuatro = 4 pts.",
            ),
        ]

        body = tk.Frame(win, bg="#111827", padx=18)
        body.pack(fill=tk.BOTH, expand=True)

        for title, desc in sections:
            tk.Label(
                body,
                text=title,
                fg="#6ee7b7",
                bg="#111827",
                font=("Sans", 10, "bold"),
                anchor="w",
            ).pack(fill=tk.X, pady=(6, 1))
            tk.Label(
                body,
                text=desc,
                fg="#e5e7eb",
                bg="#111827",
                font=("Sans", 9),
                justify=tk.LEFT,
                anchor="w",
            ).pack(fill=tk.X)

        tk.Button(
            win,
            text="Close",
            command=win.destroy,
            bg="#374151",
            fg="white",
            width=12,
            pady=4,
        ).pack(pady=12)

    def render(self):
        mano = "You" if self.state.player_is_hand else "AI"
        self.hud.config(
            text=f"You: {self.state.player_score}  |  AI: {self.state.ai_score}  |  Mano: {mano}  |  Round Pts: {self.state.current_hand_points()}"
        )

        # Disponible antes de tirar tu primera carta (también siendo pie)
        env_on = self.can_act() and not self.state.envido_resolved and not self.state.played_player
        for b in (self.b_env, self.b_real, self.b_falta):
            b.config(state=tk.NORMAL if env_on else tk.DISABLED)
        self.b_truco.config(
            text=self.state.next_truco_name().title() if self.state.truco_level < 3 else "Max",
            state=tk.NORMAL if (self.can_act() and self.state.can_call_truco("player")) else tk.DISABLED,
        )
        self.b_fold.config(state=tk.NORMAL if not self.state.round_over else tk.DISABLED)

        for w in self.resp_bar.winfo_children():
            w.destroy()
        if self.awaiting == "envido":
            tk.Button(self.resp_bar, text="Quiero", command=lambda: self.resp_envido("quiero")).pack(side=tk.LEFT, padx=3)
            tk.Button(self.resp_bar, text="No quiero", command=lambda: self.resp_envido("no quiero")).pack(side=tk.LEFT, padx=3)
            for r in get_envido_raises(self.state.envido_chain):
                tk.Button(self.resp_bar, text=r.title(), command=lambda x=r: self.resp_envido(x)).pack(side=tk.LEFT, padx=3)
        elif self.awaiting == "truco":
            tk.Button(self.resp_bar, text="Quiero", command=lambda: self.resp_truco("quiero")).pack(side=tk.LEFT, padx=3)
            tk.Button(self.resp_bar, text="No quiero", command=lambda: self.resp_truco("no quiero")).pack(side=tk.LEFT, padx=3)
            if self.state.truco_level + 1 < 3:
                rn = self.state.next_truco_name()
                tk.Button(self.resp_bar, text=rn.title(), command=lambda x=rn: self.resp_truco(x)).pack(side=tk.LEFT, padx=3)

        self.canvas.delete("all")
        for i in range(len(self.state.ai_hand)):
            x = 275 + i * 95
            self.canvas.create_rectangle(x, 15, x + 75, 105, fill="#26466d", outline="#e5e7eb", width=2)

        for i in range(3):
            sx = 250 + i * 115
            self.canvas.create_rectangle(sx, 125, sx + 75, 175, outline="#6ee7b7", dash=(2, 2))
            self.canvas.create_rectangle(sx, 182, sx + 75, 232, outline="#6ee7b7", dash=(2, 2))
            if i < len(self.state.played_ai):
                self._mini_card(sx, 125, self.state.played_ai[i])
            if i < len(self.state.played_player):
                self._mini_card(sx, 182, self.state.played_player[i])

        self.canvas.create_text(410, 255, text=self.msg, fill="#fef08a", font=("Sans", 10, "bold"))

        for i, card in enumerate(self.state.player_hand):
            x = 275 + i * 95
            tag = f"c{i}"
            self._card(x, 275, card, tag, self.can_act())
            self.canvas.tag_bind(tag, "<Button-1>", lambda _e, k=i: self.play_card(k))

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


def main():
    root = tk.Tk()
    MinimalTrucoGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()