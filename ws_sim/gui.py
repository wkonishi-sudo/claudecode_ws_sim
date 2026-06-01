import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt

from ws_sim.game import WeissSchwarz


class SimulatorGUI:
    def __init__(self, master):
        self.master = master
        master.title("WS シミュレーター")
        master.resizable(False, False)

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.single_simulation_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.single_simulation_frame, text="単一シミュレーション")

        self.graph_simulation_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.graph_simulation_frame, text="グラフ描画シミュレーション")

        self.create_single_simulation_widgets()
        self.create_graph_simulation_widgets()

    def create_single_simulation_widgets(self):
        self.attack_sequence = []

        # row 0: [ラベル + entry + チェックボックス] | [追加]
        self.damage_row_frame = ttk.Frame(self.single_simulation_frame)
        self.damage_row_frame.grid(row=0, column=0, sticky="W", padx=10, pady=10)
        self.damage_label = ttk.Label(self.damage_row_frame, text="ダメージ / ソウル値:")
        self.damage_label.pack(side=tk.LEFT)
        self.damage_entry = ttk.Entry(self.damage_row_frame, width=5)
        self.damage_entry.pack(side=tk.LEFT, padx=(4, 8))
        self.trigger_var = tk.BooleanVar(value=False)
        self.trigger_check = ttk.Checkbutton(self.damage_row_frame, text="トリガーあり", variable=self.trigger_var)
        self.trigger_check.pack(side=tk.LEFT)
        self.damage_button = tk.Button(self.single_simulation_frame, text="追加", command=self.add_damage, width=8)
        self.damage_button.grid(row=0, column=1, padx=10, pady=10)

        # row 1: [dropdown 中央] | [追加]
        self.special_attacks = WeissSchwarz.get_special_attacks()
        self.special_attack_var = tk.StringVar(value=self.special_attacks[0])
        self.special_attack_dropdown = tk.OptionMenu(self.single_simulation_frame, self.special_attack_var, *self.special_attacks, command=self.update_special_attack_params)
        self.special_attack_dropdown.grid(row=1, column=0, padx=10, pady=10)
        self.special_attack_button = tk.Button(self.single_simulation_frame, text="追加", command=self.add_special_attack, width=8)
        self.special_attack_button.grid(row=1, column=1, padx=10, pady=10)

        self.special_attack_params_frame = ttk.Frame(self.single_simulation_frame)
        self.special_attack_params_frame.grid(row=2, columnspan=2, padx=10, pady=10)

        self.attack_sequence_label = ttk.Label(self.single_simulation_frame, text="選択した行動:")
        self.attack_sequence_label.grid(row=3, column=0, sticky="W", padx=10, pady=10)
        self.attack_sequence_text = tk.Text(self.single_simulation_frame, height=10, width=40, state=tk.DISABLED)
        self.attack_sequence_text.grid(row=4, columnspan=2, padx=10, pady=10)
        self.sequence_buttons_frame = ttk.Frame(self.single_simulation_frame)
        self.sequence_buttons_frame.grid(row=5, columnspan=2, pady=10)
        self.reset_button = tk.Button(self.sequence_buttons_frame, text="リセット", command=self.reset_attack_sequence, width=8)
        self.reset_button.pack(side=tk.LEFT, padx=10)
        self.save_button = tk.Button(self.sequence_buttons_frame, text="保存", command=self.save_attack_sequence, width=8)
        self.save_button.pack(side=tk.LEFT, padx=10)
        self.load_button = tk.Button(self.sequence_buttons_frame, text="読み込み", command=self.load_attack_sequence, width=8)
        self.load_button.pack(side=tk.LEFT, padx=10)

        self.deck_size_label = ttk.Label(self.single_simulation_frame, text="山札 (CX/合計):")
        self.deck_size_label.grid(row=6, column=0, sticky="W", padx=10, pady=10)
        self.deck_size_entry = ttk.Entry(self.single_simulation_frame, width=10)
        self.deck_size_entry.grid(row=6, column=1, padx=10, pady=10)
        self.deck_size_entry.insert(0, "5/20")

        self.waiting_room_size_label = ttk.Label(self.single_simulation_frame, text="控え室 (CX/合計):")
        self.waiting_room_size_label.grid(row=7, column=0, sticky="W", padx=10, pady=10)
        self.waiting_room_size_entry = ttk.Entry(self.single_simulation_frame, width=10)
        self.waiting_room_size_entry.grid(row=7, column=1, padx=10, pady=10)
        self.waiting_room_size_entry.insert(0, "3/10")

        self.level_clock_label = ttk.Label(self.single_simulation_frame, text="レベル-クロック:")
        self.level_clock_label.grid(row=8, column=0, sticky="W", padx=10, pady=10)
        self.level_clock_entry = ttk.Entry(self.single_simulation_frame, width=5)
        self.level_clock_entry.grid(row=8, column=1, padx=10, pady=10)
        self.level_clock_entry.insert(0, "3-0")

        self.atk_deck_label = ttk.Label(self.single_simulation_frame, text="攻撃側山札 (ソウルトリガー/合計):")
        self.atk_deck_label.grid(row=9, column=0, sticky="W", padx=10, pady=10)
        self.atk_deck_entry = ttk.Entry(self.single_simulation_frame, width=10)
        self.atk_deck_entry.grid(row=9, column=1, padx=10, pady=10)
        self.atk_deck_entry.insert(0, "0/20")

        self.simulate_button = tk.Button(self.single_simulation_frame, text="シミュレーション実行", command=self.simulate, width=20)
        self.simulate_button.grid(row=10, columnspan=2, padx=10, pady=20)

        self.result_label = ttk.Label(self.single_simulation_frame, text="", justify="left")
        self.result_label.grid(row=11, columnspan=2, padx=10, pady=10)

        self.update_special_attack_params(self.special_attacks[0])

    def add_damage(self):
        damage = self.damage_entry.get()
        if damage:
            if self.trigger_var.get() and not damage.endswith("t"):
                entry = f"{damage}t"
            else:
                entry = damage
            label = f"アタック: {entry[:-1]} + トリガー" if entry.endswith("t") else f"ダメージ: {entry}"
            self.attack_sequence.append(entry)
            self.attack_sequence_text.configure(state=tk.NORMAL)
            self.attack_sequence_text.insert(tk.END, f"{label}\n")
            self.attack_sequence_text.configure(state=tk.DISABLED)
            self.damage_entry.delete(0, tk.END)

    def update_special_attack_params(self, special_attack):
        for widget in self.special_attack_params_frame.winfo_children():
            widget.destroy()
        labels, default_values = WeissSchwarz.get_special_attack_params(special_attack)
        self.create_special_attack_params(labels, default_values)

    def create_special_attack_params(self, labels, default_values):
        self.special_attack_param_entries = []
        for i, (label, default_value) in enumerate(zip(labels, default_values)):
            lbl = ttk.Label(self.special_attack_params_frame, text=label)
            lbl.grid(row=i, column=0, sticky="W")
            entry = ttk.Entry(self.special_attack_params_frame)
            entry.grid(row=i, column=1)
            entry.insert(0, str(default_value))
            self.special_attack_param_entries.append(entry)

    def add_special_attack(self):
        special_attack = self.special_attack_var.get()
        params = [entry.get() for entry in self.special_attack_param_entries]
        attack_string = f"{special_attack} {' '.join(params)}"
        self.attack_sequence.append(attack_string)
        self.attack_sequence_text.configure(state=tk.NORMAL)
        self.attack_sequence_text.insert(tk.END, f"詰め能力: {attack_string}\n")
        self.attack_sequence_text.configure(state=tk.DISABLED)

    def reset_attack_sequence(self):
        self.attack_sequence = []
        self.attack_sequence_text.configure(state=tk.NORMAL)
        self.attack_sequence_text.delete(1.0, tk.END)
        self.attack_sequence_text.configure(state=tk.DISABLED)

    def save_attack_sequence(self):
        if not self.attack_sequence:
            messagebox.showwarning("保存失敗", "行動シーケンスが空です。")
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")],
            title="行動シーケンスを保存"
        )
        if not filepath:
            return
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"attack_sequence": self.attack_sequence}, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("保存完了", f"保存しました:\n{filepath}")

    def load_attack_sequence(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")],
            title="行動シーケンスを読み込み"
        )
        if not filepath:
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            sequences = data.get("attack_sequence", [])
            self.reset_attack_sequence()
            for item in sequences:
                self.attack_sequence.append(item)
                self.attack_sequence_text.configure(state=tk.NORMAL)
                args = item.split()
                if args[0] in WeissSchwarz.get_special_attacks():
                    self.attack_sequence_text.insert(tk.END, f"詰め能力: {item}\n")
                elif args[0].endswith("t"):
                    self.attack_sequence_text.insert(tk.END, f"アタック: {args[0][:-1]} + トリガー\n")
                else:
                    self.attack_sequence_text.insert(tk.END, f"ダメージ: {item}\n")
                self.attack_sequence_text.configure(state=tk.DISABLED)
            messagebox.showinfo("読み込み完了", f"読み込みました:\n{filepath}")
        except Exception as e:
            messagebox.showerror("読み込み失敗", f"ファイルの読み込みに失敗しました。\n{e}")

    def simulate(self):
        cx_count, deck_size = map(int, self.deck_size_entry.get().split("/"))
        waiting_room_cx_count, waiting_room_size = map(int, self.waiting_room_size_entry.get().split("/"))
        level_count, clock_count = map(int, self.level_clock_entry.get().split("-"))
        atk_soul_triggers, atk_deck_size = map(int, self.atk_deck_entry.get().split("/"))

        simulations = 100000
        total_deaths = 0
        total_damage = 0

        deck = [0] * (deck_size - cx_count) + [1] * cx_count
        waiting_room = [0] * (waiting_room_size - waiting_room_cx_count) + [1] * waiting_room_cx_count

        for _ in range(simulations):
            ws = WeissSchwarz(deck.copy(), waiting_room.copy(), level_count, clock_count,
                              atk_soul_triggers=atk_soul_triggers, atk_deck_size=atk_deck_size)
            is_dead, damage_dealt = ws.simulate_attacks(self.attack_sequence)
            if is_dead:
                total_deaths += 1
            total_damage += damage_dealt

        death_rate = total_deaths / simulations
        expected_damage = total_damage / simulations
        self.result_label.configure(
            text=f"リーサル率 (10万回シミュレーション): {death_rate:.4%}\n"
                 f"打点期待値 (10万回シミュレーション): {expected_damage:.4f}"
        )

    # ── グラフ描画タブ ──────────────────────────────────────────

    def create_graph_simulation_widgets(self):
        self.graph_attack_sequence = []

        # row 0: [ラベル + entry + チェックボックス] | [追加]
        self.graph_damage_row_frame = ttk.Frame(self.graph_simulation_frame)
        self.graph_damage_row_frame.grid(row=0, column=0, sticky="W", padx=10, pady=10)
        self.graph_damage_label = ttk.Label(self.graph_damage_row_frame, text="ダメージ / ソウル値:")
        self.graph_damage_label.pack(side=tk.LEFT)
        self.graph_damage_entry = ttk.Entry(self.graph_damage_row_frame, width=5)
        self.graph_damage_entry.pack(side=tk.LEFT, padx=(4, 8))
        self.graph_trigger_var = tk.BooleanVar(value=False)
        self.graph_trigger_check = ttk.Checkbutton(self.graph_damage_row_frame, text="トリガーあり", variable=self.graph_trigger_var)
        self.graph_trigger_check.pack(side=tk.LEFT)
        self.graph_damage_button = tk.Button(self.graph_simulation_frame, text="追加", command=self.add_graph_damage, width=8)
        self.graph_damage_button.grid(row=0, column=1, padx=10, pady=10)

        # row 1: [dropdown 中央] | [追加]
        self.graph_special_attacks = WeissSchwarz.get_special_attacks()
        self.graph_special_attack_var = tk.StringVar(value=self.graph_special_attacks[0])
        self.graph_special_attack_dropdown = tk.OptionMenu(self.graph_simulation_frame, self.graph_special_attack_var, *self.graph_special_attacks, command=self.update_graph_special_attack_params)
        self.graph_special_attack_dropdown.grid(row=1, column=0, padx=10, pady=10)
        self.graph_special_attack_button = tk.Button(self.graph_simulation_frame, text="追加", command=self.add_graph_special_attack, width=8)
        self.graph_special_attack_button.grid(row=1, column=1, padx=10, pady=10)

        self.graph_special_attack_params_frame = ttk.Frame(self.graph_simulation_frame)
        self.graph_special_attack_params_frame.grid(row=2, columnspan=2, padx=10, pady=10)

        self.graph_attack_sequence_label = ttk.Label(self.graph_simulation_frame, text="選択した行動:")
        self.graph_attack_sequence_label.grid(row=3, column=0, sticky="W", padx=10, pady=10)
        self.graph_attack_sequence_text = tk.Text(self.graph_simulation_frame, height=10, width=40, state=tk.DISABLED)
        self.graph_attack_sequence_text.grid(row=4, columnspan=2, padx=10, pady=10)
        self.graph_sequence_buttons_frame = ttk.Frame(self.graph_simulation_frame)
        self.graph_sequence_buttons_frame.grid(row=5, columnspan=2, pady=10)
        self.graph_reset_button = tk.Button(self.graph_sequence_buttons_frame, text="リセット", command=self.reset_graph_attack_sequence, width=8)
        self.graph_reset_button.pack(side=tk.LEFT, padx=10)
        self.graph_save_button = tk.Button(self.graph_sequence_buttons_frame, text="保存", command=self.save_graph_attack_sequence, width=8)
        self.graph_save_button.pack(side=tk.LEFT, padx=10)
        self.graph_load_button = tk.Button(self.graph_sequence_buttons_frame, text="読み込み", command=self.load_graph_attack_sequence, width=8)
        self.graph_load_button.pack(side=tk.LEFT, padx=10)

        self.graph_level_clock_label = ttk.Label(self.graph_simulation_frame, text="レベル-クロック:")
        self.graph_level_clock_label.grid(row=6, column=0, sticky="W", padx=10, pady=10)
        self.graph_level_clock_entry = ttk.Entry(self.graph_simulation_frame, width=5)
        self.graph_level_clock_entry.grid(row=6, column=1, padx=10, pady=10)
        self.graph_level_clock_entry.insert(0, "3-0")

        self.graph_other_area_label = ttk.Label(self.graph_simulation_frame, text="別領域 (CX/合計):")
        self.graph_other_area_label.grid(row=7, column=0, sticky="W", padx=10, pady=10)
        self.graph_other_area_entry = ttk.Entry(self.graph_simulation_frame, width=10)
        self.graph_other_area_entry.grid(row=7, column=1, padx=10, pady=10)
        self.graph_other_area_entry.insert(0, "0/10")

        self.graph_atk_deck_label = ttk.Label(self.graph_simulation_frame, text="攻撃側山札 (ソウルトリガー/合計):")
        self.graph_atk_deck_label.grid(row=8, column=0, sticky="W", padx=10, pady=10)
        self.graph_atk_deck_entry = ttk.Entry(self.graph_simulation_frame, width=10)
        self.graph_atk_deck_entry.grid(row=8, column=1, padx=10, pady=10)
        self.graph_atk_deck_entry.insert(0, "0/20")

        self.graph_simulate_button = tk.Button(self.graph_simulation_frame, text="グラフ描画", command=self.simulate_graph, width=20)
        self.graph_simulate_button.grid(row=9, columnspan=2, padx=10, pady=20)

        self.update_graph_special_attack_params(self.graph_special_attacks[0])

    def add_graph_damage(self):
        damage = self.graph_damage_entry.get()
        if damage:
            if self.graph_trigger_var.get() and not damage.endswith("t"):
                entry = f"{damage}t"
            else:
                entry = damage
            label = f"アタック: {entry[:-1]} + トリガー" if entry.endswith("t") else f"ダメージ: {entry}"
            self.graph_attack_sequence.append(entry)
            self.graph_attack_sequence_text.configure(state=tk.NORMAL)
            self.graph_attack_sequence_text.insert(tk.END, f"{label}\n")
            self.graph_attack_sequence_text.configure(state=tk.DISABLED)
            self.graph_damage_entry.delete(0, tk.END)

    def update_graph_special_attack_params(self, special_attack):
        for widget in self.graph_special_attack_params_frame.winfo_children():
            widget.destroy()
        labels, default_values = WeissSchwarz.get_special_attack_params(special_attack)
        self.create_graph_special_attack_params(labels, default_values)

    def create_graph_special_attack_params(self, labels, default_values):
        self.graph_special_attack_param_entries = []
        for i, (label, default_value) in enumerate(zip(labels, default_values)):
            lbl = ttk.Label(self.graph_special_attack_params_frame, text=label)
            lbl.grid(row=i, column=0, sticky="W")
            entry = ttk.Entry(self.graph_special_attack_params_frame)
            entry.grid(row=i, column=1)
            entry.insert(0, str(default_value))
            self.graph_special_attack_param_entries.append(entry)

    def add_graph_special_attack(self):
        special_attack = self.graph_special_attack_var.get()
        params = [entry.get() for entry in self.graph_special_attack_param_entries]
        attack_string = f"{special_attack} {' '.join(params)}"
        self.graph_attack_sequence.append(attack_string)
        self.graph_attack_sequence_text.configure(state=tk.NORMAL)
        self.graph_attack_sequence_text.insert(tk.END, f"詰め能力: {attack_string}\n")
        self.graph_attack_sequence_text.configure(state=tk.DISABLED)

    def reset_graph_attack_sequence(self):
        self.graph_attack_sequence = []
        self.graph_attack_sequence_text.configure(state=tk.NORMAL)
        self.graph_attack_sequence_text.delete(1.0, tk.END)
        self.graph_attack_sequence_text.configure(state=tk.DISABLED)

    def save_graph_attack_sequence(self):
        if not self.graph_attack_sequence:
            messagebox.showwarning("保存失敗", "行動シーケンスが空です。")
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")],
            title="行動シーケンスを保存"
        )
        if not filepath:
            return
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"attack_sequence": self.graph_attack_sequence}, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("保存完了", f"保存しました:\n{filepath}")

    def load_graph_attack_sequence(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")],
            title="行動シーケンスを読み込み"
        )
        if not filepath:
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            sequences = data.get("attack_sequence", [])
            self.reset_graph_attack_sequence()
            for item in sequences:
                self.graph_attack_sequence.append(item)
                self.graph_attack_sequence_text.configure(state=tk.NORMAL)
                args = item.split()
                if args[0] in WeissSchwarz.get_special_attacks():
                    self.graph_attack_sequence_text.insert(tk.END, f"詰め能力: {item}\n")
                elif args[0].endswith("t"):
                    self.graph_attack_sequence_text.insert(tk.END, f"アタック: {args[0][:-1]} + トリガー\n")
                else:
                    self.graph_attack_sequence_text.insert(tk.END, f"ダメージ: {item}\n")
                self.graph_attack_sequence_text.configure(state=tk.DISABLED)
            messagebox.showinfo("読み込み完了", f"読み込みました:\n{filepath}")
        except Exception as e:
            messagebox.showerror("読み込み失敗", f"ファイルの読み込みに失敗しました。\n{e}")

    def simulate_graph(self):
        level_count, clock_count = map(int, self.graph_level_clock_entry.get().split("-"))
        other_area_cx_count, other_area_count = map(int, self.graph_other_area_entry.get().split("/"))
        atk_soul_triggers, atk_deck_size = map(int, self.graph_atk_deck_entry.get().split("/"))

        results = self.simulate_all_decks(level_count, clock_count, other_area_count, other_area_cx_count, 10000,
                                          atk_soul_triggers, atk_deck_size)

        cx_counts = list(range(8 - other_area_cx_count, -1, -1))
        deck_sizes_dict = {cx: list(range(max(cx, 1), 51 - level_count - clock_count - other_area_count)) for cx in cx_counts}
        max_deck_size = 50 - level_count - clock_count - other_area_count

        death_rates = [[0] * (51 - level_count - clock_count - other_area_count - max(cx, 1)) for cx in cx_counts]
        expected_damages = [[0] * (51 - level_count - clock_count - other_area_count - max(cx, 1)) for cx in cx_counts]

        for cx_count, deck_size, death_rate, expected_damage in results:
            death_rates[8 - other_area_cx_count - cx_count][max_deck_size - deck_size] = death_rate
            expected_damages[8 - other_area_cx_count - cx_count][max_deck_size - deck_size] = expected_damage

        self.plot_graph(cx_counts, deck_sizes_dict, death_rates, expected_damages)

    def simulate_all_decks(self, level_count, clock_count, other_area_count, other_area_cx_count, simulations,
                           atk_soul_triggers=0, atk_deck_size=20):
        results = []
        for cx_count in range(8 - other_area_cx_count, -1, -1):
            min_deck_size = max(cx_count, 1)
            for deck_size in range(50 - level_count - clock_count - other_area_count, min_deck_size - 1, -1):
                waiting_room_size = 50 - deck_size - level_count - clock_count - other_area_count
                waiting_room_cx_count = 8 - cx_count - other_area_cx_count
                deck = [0] * (deck_size - cx_count) + [1] * cx_count
                waiting_room = [0] * (waiting_room_size - waiting_room_cx_count) + [1] * waiting_room_cx_count

                total_deaths = 0
                total_damage = 0
                for _ in range(simulations):
                    ws = WeissSchwarz(deck.copy(), waiting_room.copy(), level_count, clock_count,
                                      other_area_count, other_area_cx_count,
                                      atk_soul_triggers=atk_soul_triggers, atk_deck_size=atk_deck_size)
                    is_dead, damage_dealt = ws.simulate_attacks(self.graph_attack_sequence)
                    if is_dead:
                        total_deaths += 1
                    total_damage += damage_dealt

                results.append((cx_count, deck_size, total_deaths / simulations, total_damage / simulations))
        return results

    def plot_graph(self, cx_counts, deck_sizes_dict, death_rates, expected_damages):
        plt.figure(figsize=(12, 6))

        plt.subplot(1, 2, 1)
        for cx_count, death_rate_row in zip(cx_counts, death_rates):
            plt.plot(list(reversed(deck_sizes_dict[cx_count])), death_rate_row, label=f'CX枚数: {cx_count}')
        plt.xlabel('山札枚数', fontname='MS Gothic')
        plt.ylabel('リーサル率', fontname='MS Gothic')
        plt.ylim(ymin=0)
        plt.legend(prop={'family': 'MS Gothic'})
        plt.grid()
        plt.gca().invert_xaxis()

        plt.subplot(1, 2, 2)
        for cx_count, expected_damage_row in zip(cx_counts, expected_damages):
            plt.plot(list(reversed(deck_sizes_dict[cx_count])), expected_damage_row, label=f'CX枚数: {cx_count}')
        plt.xlabel('山札枚数', fontname='MS Gothic')
        plt.ylabel('打点期待値', fontname='MS Gothic')
        plt.ylim(ymin=0)
        plt.legend(prop={'family': 'MS Gothic'})
        plt.grid()
        plt.gca().invert_xaxis()

        plt.tight_layout()
        plt.show()
