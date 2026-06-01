import random
from ws_sim.abilities import AbilityMixin


class WeissSchwarz(AbilityMixin):
    def __init__(self, deck, waiting_room, level_count, clock_count,
                 other_area_count=0, other_area_cx_count=0,
                 stock=None,
                 atk_soul_triggers=0, atk_deck_size=20):
        self.deck = deck
        self.waiting_room = waiting_room
        self.clock = [0] * clock_count
        self.level = [0] * level_count
        self.other_area = [0] * (other_area_count - other_area_cx_count) + [1] * other_area_cx_count
        self.stock = stock if stock is not None else []
        self.initial_level = level_count
        self.initial_clock = clock_count
        self.atk_soul_triggers = atk_soul_triggers
        self.atk_deck_size = atk_deck_size
        random.shuffle(self.deck)

    def flip_trigger(self):
        """攻撃側の山札からトリガーを1枚めくる。ソウルトリガーなら1、それ以外は0を返す。"""
        if self.atk_deck_size == 0:
            return 0
        hit = random.random() < self.atk_soul_triggers / self.atk_deck_size
        if hit:
            self.atk_soul_triggers -= 1
        self.atk_deck_size -= 1
        return 1 if hit else 0

    def attack(self, soul):
        """トリガーをめくり、ソウル値 + トリガー結果のダメージを与える。"""
        total = soul + self.flip_trigger()
        self.damage(total)

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
            self.refresh()
            resolution.append(self.deck.pop(0))

        cancel_index = None
        for i, card in enumerate(resolution):
            if card == 1:
                cancel_index = i
                break

        if cancel_index is not None:
            self.waiting_room.extend(resolution[:cancel_index + 1])
            self.deck = resolution[cancel_index + 1:] + self.deck
        else:
            self.clock.extend(resolution)

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
            func_args = args[1:]

            # 「2t」形式: トリガーありアタック
            if func_name.endswith("t") and func_name[:-1].lstrip("-").isdigit():
                try:
                    self.attack(int(func_name[:-1]))
                except ValueError:
                    print(f"Invalid soul value: {func_name}")
                continue

            func = getattr(self, func_name, None)
            if func:
                try:
                    func(*[int(arg) for arg in func_args])
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
        damage_dealt = (7 * len(self.level) + len(self.clock)
                        - (7 * self.initial_level + self.initial_clock))
        return is_dead, damage_dealt
