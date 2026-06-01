import random
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class WeissSchwarz:
    def __init__(self, deck, waiting_room, level_count, clock_count, other_area_count=0, other_area_cx_count=0):
        self.deck = deck
        self.waiting_room = waiting_room
        self.clock = [0] * clock_count
        self.level = [0] * level_count
        self.other_area = [0] * (other_area_count - other_area_cx_count) + [1] * other_area_cx_count
        self.initial_level = level_count
        self.initial_clock = clock_count
        random.shuffle(self.deck)

    def refresh(self):
        if not self.deck:
            self.deck = self.waiting_room
            self.waiting_room = []
            random.shuffle(self.deck)
            self.clock.append(self.deck.pop(0))
            self.level_up()

    def damage(self, x):
        resolution = []

        for _ in range(x):
            self.refresh()  # リフレッシュ処理を呼び出す
            resolution.append(self.deck.pop(0))

        cancel_index = None
        for i, card in enumerate(resolution):
            if card == 1:
                cancel_index = i
                break

        if cancel_index is not None:
            self.waiting_room.extend(resolution[:cancel_index+1])
            self.deck = resolution[cancel_index+1:] + self.deck
        else:
            self.clock.extend(resolution)

        self.refresh()  # 解決後にリフレッシュ処理を呼び出す
        self.level_up()

    def touya(self, n=6, m=1):
        """
        山下から捲る枚数: n
        一度に与えるダメージ: m
        """
        cx_count = 0
        for _ in range(n):
            self.refresh()  # リフレッシュ処理を呼び出す
            card = self.deck.pop()
            self.waiting_room.append(card)
            if card == 1:
                cx_count += 1

        for _ in range(cx_count):
            self.damage(m)

    def miku(self, n=4, m=1, k=2):
        """
        山下から捲る枚数: n
        一度に与えるダメージ: m
        ダメージを与える回数: k
        """
        cx_count = 0
        for _ in range(n):
            self.refresh()  # リフレッシュ処理を呼び出す
            card = self.deck.pop()
            self.waiting_room.append(card)
            if card == 1:
                cx_count += 1

        if cx_count > 0:
            for _ in range(k):
                self.damage(m)

    def michiru(self, n=4, m=1):
        """
        山下から捲る枚数: n
        ダメージ: m
        """
        cx_count = 0
        for _ in range(n):
            self.refresh()
            card = self.deck.pop()
            self.waiting_room.append(card)
            if card == 1:
                cx_count += 1

        self.damage(cx_count * m)

    def song_for_all(self, n=3):
        """
        山札から捲る枚数: n
        """
        revealed_cards = []
        cx_count = 0
        
        for _ in range(min(n, len(self.deck))):
            card = self.deck.pop()
            revealed_cards.append(card)
            if card == 1:
                cx_count += 1
        
        self.deck.extend(revealed_cards[::-1])
        random.shuffle(self.deck)
        
        for _ in range(cx_count):
            card = self.deck.pop(0)
            self.clock.append(card)
            self.refresh()
            self.level_up()

    def level_up(self):
        if len(self.clock) >= 7:
            self.level.append(0)
            self.waiting_room.extend(self.clock[:7])
            self.clock = self.clock[7:]

    def is_dead(self):
        return len(self.level) >= 4

    def simulate_attacks(self, attack_sequence):
        for attack in attack_sequence:
            args = attack.split()
            func_name = args[0]
            func_args = args[1:]  # 関数の引数を取得
            func = getattr(self, func_name, None)
            if func:
                try:
                    func(*[int(arg) for arg in func_args])  # 引数をアンパックして関数に渡す
                except TypeError:
                    print(f"Invalid number of arguments for function: {func_name}")
                    continue
            else:
                try:
                    self.damage(int(func_name))
                except ValueError:
                    print(f"Unknown function or invalid input: {func_name}")
                    continue

        is_dead = self.is_dead()
        damage_dealt = 7 * len(self.level) + len(self.clock) - (7 * self.initial_level + self.initial_clock)

        return is_dead, damage_dealt

    @staticmethod
    def get_special_attacks():
        return ["touya", "miku", "michiru", "song_for_all"]

    @staticmethod
    def get_special_attack_params(special_attack):
        func = getattr(WeissSchwarz, special_attack, None)
        if func:
            docstring = func.__doc__
            if docstring:
                param_lines = [line.strip() for line in docstring.split("\n") if ":" in line]
                labels = [line.split(":")[0].strip() for line in param_lines]
                default_values = func.__defaults__ if func.__defaults__ else []
                return labels, default_values
        return [], []

class SimulatorGUI:
    def __init__(self, master):
        self.master = master
        master.title("WS シミュレーター")
        master.resizable(False, False)  # ウィンドウのサイズ変更を禁止

        # タブの作成
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # ①のシミュレーション画面
        self.single_simulation_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.single_simulation_frame, text="単一シミュレーション")

        # ②のグラフ描画シミュレーション画面
        self.graph_simulation_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.graph_simulation_frame, text="グラフ描画シミュレーション")

        # ①のシミュレーション画面の構築
        self.create_single_simulation_widgets()

        # ②のグラフ描画シミュレーション画面の構築
        self.create_graph_simulation_widgets()

    def create_single_simulation_widgets(self):
        self.attack_sequence = []

        self.damage_label = ttk.Label(self.single_simulation_frame, text="ダメージ:")
        self.damage_label.grid(row=0, column=0, sticky="W", padx=10, pady=10)
        self.damage_entry = ttk.Entry(self.single_simulation_frame, width=5)
        self.damage_entry.grid(row=0, column=1, padx=10, pady=10)
        self.damage_button = tk.Button(self.single_simulation_frame, text="追加", command=self.add_damage, width=8)
        self.damage_button.grid(row=0, column=2, padx=10, pady=10)

        self.special_attacks = WeissSchwarz.get_special_attacks()
        self.special_attack_var = tk.StringVar(value=self.special_attacks[0])
        self.special_attack_dropdown = tk.OptionMenu(self.single_simulation_frame, self.special_attack_var, *self.special_attacks, command=self.update_special_attack_params)
        self.special_attack_dropdown.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
        self.special_attack_button = tk.Button(self.single_simulation_frame, text="追加", command=self.add_special_attack, width=8)
        self.special_attack_button.grid(row=1, column=2, padx=10, pady=10)

        self.special_attack_params_frame = ttk.Frame(self.single_simulation_frame)
        self.special_attack_params_frame.grid(row=2, columnspan=3, padx=10, pady=10)

        self.attack_sequence_label = ttk.Label(self.single_simulation_frame, text="選択した行動:")
        self.attack_sequence_label.grid(row=3, column=0, sticky="W", padx=10, pady=10)
        self.attack_sequence_text = tk.Text(self.single_simulation_frame, height=10, width=40, state=tk.DISABLED)
        self.attack_sequence_text.grid(row=4, columnspan=3, padx=10, pady=10)
        self.reset_button = tk.Button(self.single_simulation_frame, text="リセット", command=self.reset_attack_sequence, width=8)
        self.reset_button.grid(row=5, columnspan=3, padx=10, pady=10)

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

        self.simulate_button = tk.Button(self.single_simulation_frame, text="シミュレーション実行", command=self.simulate, width=20)
        self.simulate_button.grid(row=9, columnspan=3, padx=10, pady=20)

        self.result_label = ttk.Label(self.single_simulation_frame, text="", justify="left")
        self.result_label.grid(row=10, columnspan=3, padx=10, pady=10)

        self.update_special_attack_params(self.special_attacks[0])

    def add_damage(self):
        damage = self.damage_entry.get()
        if damage:
            self.attack_sequence.append(damage)
            self.attack_sequence_text.configure(state=tk.NORMAL)
            self.attack_sequence_text.insert(tk.END, f"ダメージ: {damage}\n")
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
            label = ttk.Label(self.special_attack_params_frame, text=label)
            label.grid(row=i, column=0, sticky="W")
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

    def simulate(self):
        deck_size_text = self.deck_size_entry.get()
        waiting_room_size_text = self.waiting_room_size_entry.get()
        level_clock_text = self.level_clock_entry.get()

        cx_count, deck_size = map(int, deck_size_text.split("/"))
        waiting_room_cx_count, waiting_room_size = map(int, waiting_room_size_text.split("/"))
        level_count, clock_count = map(int, level_clock_text.split("-"))

        simulations = 100000

        total_deaths = 0
        total_damage = 0

        deck = [0] * (deck_size - cx_count) + [1] * cx_count
        waiting_room = [0] * (waiting_room_size - waiting_room_cx_count) + [1] * waiting_room_cx_count

        for _ in range(simulations):
            ws = WeissSchwarz(deck.copy(), waiting_room.copy(), level_count, clock_count)
            is_dead, damage_dealt = ws.simulate_attacks(self.attack_sequence)
            if is_dead:
                total_deaths += 1
            total_damage += damage_dealt

        death_rate = total_deaths / simulations
        expected_damage = total_damage / simulations

        result_text = f"リーサル率 (10万回シミュレーション): {death_rate:.4%}\n"
        result_text += f"打点期待値 (10万回シミュレーション): {expected_damage:.4f}"
        self.result_label.configure(text=result_text)

    def create_graph_simulation_widgets(self):
        self.graph_attack_sequence = []

        self.graph_damage_label = ttk.Label(self.graph_simulation_frame, text="ダメージ:")
        self.graph_damage_label.grid(row=0, column=0, sticky="W", padx=10, pady=10)
        self.graph_damage_entry = ttk.Entry(self.graph_simulation_frame, width=5)
        self.graph_damage_entry.grid(row=0, column=1, padx=10, pady=10)
        self.graph_damage_button = tk.Button(self.graph_simulation_frame, text="追加", command=self.add_graph_damage, width=8)
        self.graph_damage_button.grid(row=0, column=2, padx=10, pady=10)

        self.graph_special_attacks = WeissSchwarz.get_special_attacks()
        self.graph_special_attack_var = tk.StringVar(value=self.graph_special_attacks[0])
        self.graph_special_attack_dropdown = tk.OptionMenu(self.graph_simulation_frame, self.graph_special_attack_var, *self.graph_special_attacks, command=self.update_graph_special_attack_params)
        self.graph_special_attack_dropdown.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
        self.graph_special_attack_button = tk.Button(self.graph_simulation_frame, text="追加", command=self.add_graph_special_attack, width=8)
        self.graph_special_attack_button.grid(row=1, column=2, padx=10, pady=10)

        self.graph_special_attack_params_frame = ttk.Frame(self.graph_simulation_frame)
        self.graph_special_attack_params_frame.grid(row=2, columnspan=3, padx=10, pady=10)

        self.graph_attack_sequence_label = ttk.Label(self.graph_simulation_frame, text="選択した行動:")
        self.graph_attack_sequence_label.grid(row=3, column=0, sticky="W", padx=10, pady=10)
        self.graph_attack_sequence_text = tk.Text(self.graph_simulation_frame, height=10, width=40, state=tk.DISABLED)
        self.graph_attack_sequence_text.grid(row=4, columnspan=3, padx=10, pady=10)
        self.graph_reset_button = tk.Button(self.graph_simulation_frame, text="リセット", command=self.reset_graph_attack_sequence, width=8)
        self.graph_reset_button.grid(row=5, columnspan=3, padx=10, pady=10)

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

        self.graph_simulate_button = tk.Button(self.graph_simulation_frame, text="グラフ描画", command=self.simulate_graph, width=20)
        self.graph_simulate_button.grid(row=8, columnspan=3, padx=10, pady=20)

        self.update_graph_special_attack_params(self.graph_special_attacks[0])

    def add_graph_damage(self):
        damage = self.graph_damage_entry.get()
        if damage:
            self.graph_attack_sequence.append(damage)
            self.graph_attack_sequence_text.configure(state=tk.NORMAL)
            self.graph_attack_sequence_text.insert(tk.END, f"ダメージ: {damage}\n")
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
            label = ttk.Label(self.graph_special_attack_params_frame, text=label)
            label.grid(row=i, column=0, sticky="W")
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

    def simulate_graph(self):
        level_clock_text = self.graph_level_clock_entry.get()
        level_count, clock_count = map(int, level_clock_text.split("-"))

        other_area_text = self.graph_other_area_entry.get()
        other_area_cx_count, other_area_count = map(int, other_area_text.split("/"))

        results = self.simulate_all_decks(level_count, clock_count, other_area_count, other_area_cx_count, 10000)

        cx_counts = list(range(8 - other_area_cx_count, -1, -1))
        deck_sizes_dict = {cx_count: list(range(max(cx_count, 1), 51 - level_count - clock_count - other_area_count)) for cx_count in cx_counts}
        max_deck_size = 50 - level_count - clock_count - other_area_count

        death_rates = [[0] * (51 - level_count - clock_count - other_area_count - max(cx_count, 1)) for cx_count in cx_counts]
        expected_damages = [[0] * (51 - level_count - clock_count - other_area_count - max(cx_count, 1)) for cx_count in cx_counts]

        for cx_count, deck_size, death_rate, expected_damage in results:
            death_rates[8 - other_area_cx_count - cx_count][max_deck_size - deck_size] = death_rate
            expected_damages[8 - other_area_cx_count - cx_count][max_deck_size - deck_size] = expected_damage

        self.plot_graph(cx_counts, deck_sizes_dict, death_rates, expected_damages)

    def simulate_all_decks(self, level_count, clock_count, other_area_count, other_area_cx_count, simulations):
        results = []

        for cx_count in range(8 - other_area_cx_count, -1, -1):
            min_deck_size = max(cx_count, 1)
            for deck_size in range(50 - level_count - clock_count - other_area_count, min_deck_size - 1, -1):
                non_cx_count = 50 - cx_count - other_area_cx_count
                waiting_room_size = 50 - deck_size - level_count - clock_count - other_area_count
                waiting_room_cx_count = 8 - cx_count - other_area_cx_count
                waiting_room_non_cx_count = waiting_room_size - waiting_room_cx_count

                deck = [0] * (deck_size - cx_count) + [1] * cx_count
                waiting_room = [0] * waiting_room_non_cx_count + [1] * waiting_room_cx_count

                total_deaths = 0
                total_damage = 0

                for _ in range(simulations):
                    ws = WeissSchwarz(deck.copy(), waiting_room.copy(), level_count, clock_count, other_area_count, other_area_cx_count)
                    is_dead, damage_dealt = ws.simulate_attacks(self.graph_attack_sequence)
                    if is_dead:
                        total_deaths += 1
                    total_damage += damage_dealt

                death_rate = total_deaths / simulations
                expected_damage = total_damage / simulations

                results.append((cx_count, deck_size, death_rate, expected_damage))

        return results

    def plot_graph(self, cx_counts, deck_sizes_dict, death_rates, expected_damages):
        plt.figure(figsize=(12, 6))

        plt.subplot(1, 2, 1)
        for cx_count, death_rate_row in zip(cx_counts, death_rates):
            plt.plot(list(reversed(deck_sizes_dict[cx_count])), death_rate_row, label=f'CX枚数: {cx_count}')
        plt.xlabel('山札枚数', fontname='MS Gothic')
        plt.ylabel('リーサル率', fontname='MS Gothic')
        plt.ylim(ymin=0)
        plt.legend(prop={'family':'MS Gothic'})
        plt.grid()
        plt.gca().invert_xaxis()

        plt.subplot(1, 2, 2)
        for cx_count, expected_damage_row in zip(cx_counts, expected_damages):
            plt.plot(list(reversed(deck_sizes_dict[cx_count])), expected_damage_row, label=f'CX枚数: {cx_count}')
        plt.xlabel('山札枚数', fontname='MS Gothic')
        plt.ylabel('打点期待値', fontname='MS Gothic')
        plt.ylim(ymin=0)
        plt.legend(prop={'family':'MS Gothic'})
        plt.grid()
        plt.gca().invert_xaxis()

        plt.tight_layout()
        plt.show()

root = tk.Tk()
simulator_gui = SimulatorGUI(root)
root.mainloop()