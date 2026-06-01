class AbilityMixin:
    def touya(self, n=6, m=1):
        """
        山下から捲る枚数: n
        一度に与えるダメージ: m
        """
        cx_count = 0
        for _ in range(n):
            self.refresh()
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
            self.refresh()
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
        import random
        revealed_cards = []
        cx_count = 0

        for _ in range(min(n, len(self.deck))):
            card = self.deck.pop(0)  # 山上からめくる
            revealed_cards.append(card)
            if card == 1:
                cx_count += 1

        self.deck.extend(revealed_cards)
        random.shuffle(self.deck)

        for _ in range(cx_count):
            card = self.deck.pop(0)
            self.clock.append(card)
            self.refresh()
            self.level_up()

    def koukei(self):
        """
        """
        count = len(self.stock)
        self.waiting_room.extend(self.stock)
        self.stock = []
        for _ in range(count):
            self.refresh()
            self.stock.append(self.deck.pop(0))

    def decomp_keep_cx(self, k=1):
        """
        控え室に残すCX枚数: k
        """
        import random
        cx_in_wr = [c for c in self.waiting_room if c == 1]
        non_cx_in_wr = [c for c in self.waiting_room if c == 0]

        keep_cx_count = min(k, len(cx_in_wr))
        return_cx_count = len(cx_in_wr) - keep_cx_count

        self.waiting_room = [1] * keep_cx_count

        returned = non_cx_in_wr + [1] * return_cx_count
        self.deck = returned + self.deck
        random.shuffle(self.deck)

    def decomp_return_noncx(self, n=2):
        """
        山札に戻す非CX枚数: n
        """
        import random
        non_cx_in_wr = [c for c in self.waiting_room if c == 0]

        return_count = min(n, len(non_cx_in_wr))
        self.waiting_room = [c for c in self.waiting_room if c == 1] + non_cx_in_wr[return_count:]

        self.deck = non_cx_in_wr[:return_count] + self.deck
        random.shuffle(self.deck)

    @staticmethod
    def get_special_attacks():
        return ["touya", "miku", "michiru", "song_for_all", "koukei", "decomp_keep_cx", "decomp_return_noncx"]

    @staticmethod
    def get_special_attack_params(special_attack):
        func = getattr(AbilityMixin, special_attack, None)
        if func:
            docstring = func.__doc__
            if docstring:
                param_lines = [line.strip() for line in docstring.split("\n") if ":" in line]
                labels = [line.split(":")[0].strip() for line in param_lines]
                default_values = func.__defaults__ if func.__defaults__ else []
                return labels, default_values
        return [], []
