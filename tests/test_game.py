import pytest
from ws_sim.game import WeissSchwarz


def make_ws(deck=None, waiting_room=None, level=0, clock=0, stock=None):
    """テスト用のWeissSchwarzインスタンスを作るヘルパー。山札はシャッフルされる。"""
    deck = deck if deck is not None else [0] * 20
    waiting_room = waiting_room if waiting_room is not None else []
    return WeissSchwarz(deck, waiting_room, level, clock, stock=stock)


def make_ws_fixed(deck_cards, waiting_room=None, level=0, clock=0, stock=None):
    """山札順序を確定させたいテスト用ヘルパー。init後にdeckを上書きしてシャッフルを回避する。"""
    wr = waiting_room if waiting_room is not None else []
    ws = WeissSchwarz([0] * 20, wr, level, clock, stock=stock)
    ws.deck = deck_cards[:]
    return ws


# ── コアロジック ─────────────────────────────────────────────

class TestDamage:
    def test_damage_adds_to_clock(self):
        # 非CXのみの山→全部クロックに乗る
        ws = make_ws(deck=[0] * 20)
        ws.damage(3)
        assert len(ws.clock) == 3

    def test_cancel_stops_damage(self):
        # 1枚目がCX → キャンセル。クロックは増えない
        ws = make_ws_fixed([1, 0, 0] + [0] * 17)
        ws.damage(3)
        assert len(ws.clock) == 0

    def test_cancel_mid_sequence(self):
        # 2枚目がCX → ダメージ解決全体がキャンセル（CX以前の非CXもクロックに乗らない）
        ws = make_ws_fixed([0, 1, 0] + [0] * 17)
        ws.damage(3)
        assert len(ws.clock) == 0

    def test_cancel_returns_remaining_to_deck(self):
        # キャンセル後の残りカードが山頭に戻る
        ws = make_ws_fixed([0, 1, 0] + [0] * 17)
        ws.damage(3)
        # 解決後: 控え室[0,1]、山頭に[0]が戻る
        assert ws.deck[0] == 0


class TestRefresh:
    def test_refresh_moves_waiting_room_to_deck(self):
        ws = make_ws(deck=[], waiting_room=[0, 0, 1])
        ws.refresh()
        assert len(ws.deck) >= 1  # 1枚はクロックに乗る
        assert ws.waiting_room == []

    def test_refresh_clock_gets_one_card(self):
        ws = make_ws(deck=[], waiting_room=[0, 0, 0])
        ws.refresh()
        assert len(ws.clock) == 1

    def test_no_refresh_when_deck_not_empty(self):
        ws = make_ws(deck=[0], waiting_room=[0, 0])
        ws.refresh()
        assert len(ws.waiting_room) == 2  # 変化なし


class TestLevelUp:
    def test_level_up_at_7_clock(self):
        ws = make_ws(deck=[0] * 20)
        ws.clock = [0] * 7
        ws.level_up()
        assert len(ws.level) == 1
        assert len(ws.clock) == 0

    def test_level_up_sends_7_to_waiting_room(self):
        ws = make_ws(deck=[0] * 20)
        ws.clock = [0] * 7
        ws.level_up()
        assert len(ws.waiting_room) == 7

    def test_no_level_up_below_7(self):
        ws = make_ws(deck=[0] * 20)
        ws.clock = [0] * 6
        ws.level_up()
        assert len(ws.level) == 0

    def test_is_dead_at_level_4(self):
        ws = make_ws(deck=[0] * 20)
        ws.level = [0, 0, 0, 0]
        assert ws.is_dead()

    def test_not_dead_at_level_3(self):
        ws = make_ws(deck=[0] * 20)
        ws.level = [0, 0, 0]
        assert not ws.is_dead()


# ── 詰め能力 ─────────────────────────────────────────────────

class TestTouya:
    def test_cx_causes_damage(self):
        # 山下6枚にCX2枚 → 2ダメージ。リフレッシュを防ぐため十分な山を用意
        ws = make_ws(deck=[0] * 20, waiting_room=[0] * 10)
        ws.deck = [0] * 14 + [0, 0, 0, 0, 1, 1]
        ws.touya(n=6, m=1)
        assert len(ws.clock) == 2

    def test_no_cx_no_damage(self):
        ws = make_ws(deck=[0] * 20, waiting_room=[0] * 10)
        ws.touya(n=6, m=1)
        assert len(ws.clock) == 0

    def test_damage_multiplier(self):
        # CX1枚 × m=3 → 3ダメージ。リフレッシュを防ぐため十分な山を用意
        ws = make_ws(deck=[0] * 20, waiting_room=[0] * 10)
        ws.deck = [0] * 19 + [1]
        ws.touya(n=6, m=3)
        assert len(ws.clock) == 3


class TestMiku:
    def test_cx_found_causes_k_damage(self):
        # 山下4枚にCX1枚 → k=2回 m=1ダメージ
        ws = make_ws(deck=[0] * 20, waiting_room=[0] * 10)
        ws.deck = [0] * 19 + [1]
        ws.miku(n=4, m=1, k=2)
        assert len(ws.clock) == 2

    def test_no_cx_no_damage(self):
        ws = make_ws(deck=[0] * 20, waiting_room=[0] * 10)
        ws.miku(n=4, m=1, k=2)
        assert len(ws.clock) == 0


class TestMichiru:
    def test_cx_count_times_m_damage(self):
        # 山下4枚にCX2枚 × m=2 → 4ダメージ
        ws = make_ws(deck=[0] * 20, waiting_room=[0] * 10)
        ws.deck = [0] * 18 + [1, 1]
        ws.michiru(n=4, m=2)
        assert len(ws.clock) == 4

    def test_no_cx_zero_damage(self):
        # CX0枚 → damage(0)。山が残っているのでリフレッシュは起きない
        ws = make_ws(deck=[0] * 20, waiting_room=[0] * 10)
        ws.michiru(n=4, m=2)
        assert len(ws.clock) == 0


class TestSongForAll:
    def test_cx_goes_to_clock(self):
        # 山上3枚にCX1枚 → クロック1枚増
        ws = make_ws_fixed([1, 0, 0] + [0] * 17)
        ws.song_for_all(n=3)
        assert len(ws.clock) == 1

    def test_no_cx_no_clock(self):
        ws = make_ws(deck=[0] * 20)
        ws.song_for_all(n=3)
        assert len(ws.clock) == 0

    def test_deck_size_preserved(self):
        # めくったカードはシャッフルして山に戻るので総枚数変化なし（クロック分は減る）
        ws = make_ws(deck=[0] * 20)
        ws.song_for_all(n=3)
        assert len(ws.deck) + len(ws.clock) == 20


# ── koukei ───────────────────────────────────────────────────

class TestKoukei:
    def test_stock_moves_to_waiting_room(self):
        stock = [0] * 8 + [1] * 2  # 10枚
        ws = make_ws(deck=[0] * 20, waiting_room=[], stock=stock)
        ws.koukei()
        assert len(ws.waiting_room) == 10

    def test_deck_top_fills_stock(self):
        stock = [0] * 10
        ws = make_ws(deck=[0] * 20, stock=stock)
        ws.koukei()
        assert len(ws.stock) == 10
        assert len(ws.deck) == 10

    def test_total_card_count_preserved(self):
        stock = [0] * 5 + [1] * 2  # 7枚
        ws = make_ws(deck=[0] * 15, waiting_room=[0] * 5, stock=stock)
        before = len(ws.deck) + len(ws.waiting_room) + len(ws.stock)
        ws.koukei()
        after = len(ws.deck) + len(ws.waiting_room) + len(ws.stock)
        assert before == after

    def test_cx_in_stock_goes_to_waiting_room(self):
        stock = [1, 1, 0]  # CX2枚
        ws = make_ws(deck=[0] * 20, stock=stock)
        ws.koukei()
        cx_in_wr = sum(ws.waiting_room)
        assert cx_in_wr == 2

    def test_empty_stock_does_nothing(self):
        ws = make_ws(deck=[0] * 20, stock=[])
        ws.koukei()
        assert ws.stock == []
        assert len(ws.deck) == 20


# ── 逆圧縮系 ─────────────────────────────────────────────────

class TestDecompKeepCx:
    def test_keeps_k_cx_in_waiting_room(self):
        ws = make_ws(deck=[0] * 10, waiting_room=[0] * 8 + [1] * 3)
        ws.decomp_keep_cx(k=1)
        assert ws.waiting_room == [1]

    def test_non_cx_return_to_deck(self):
        ws = make_ws(deck=[0] * 10, waiting_room=[0] * 5 + [1] * 2)
        before_total = len(ws.deck) + len(ws.waiting_room)
        ws.decomp_keep_cx(k=1)
        after_total = len(ws.deck) + len(ws.waiting_room)
        assert before_total == after_total

    def test_fewer_cx_than_k_keeps_all(self):
        # 控え室にCX1枚しかないのにk=2 → 1枚だけ残る
        ws = make_ws(deck=[0] * 10, waiting_room=[0] * 5 + [1] * 1)
        ws.decomp_keep_cx(k=2)
        assert ws.waiting_room == [1]

    def test_k2_keeps_two_cx(self):
        ws = make_ws(deck=[0] * 10, waiting_room=[0] * 5 + [1] * 3)
        ws.decomp_keep_cx(k=2)
        assert sum(ws.waiting_room) == 2
        assert len(ws.waiting_room) == 2


class TestDecompReturnNoncx:
    def test_returns_n_noncx_to_deck(self):
        ws = make_ws(deck=[0] * 10, waiting_room=[0] * 5 + [1] * 3)
        ws.decomp_return_noncx(n=2)
        assert sum(ws.waiting_room) == 3  # CXはそのまま
        assert len(ws.waiting_room) == 3 + (5 - 2)

    def test_fewer_noncx_than_n_returns_all(self):
        # 非CX1枚しかないのにn=2 → 1枚だけ戻る
        ws = make_ws(deck=[0] * 10, waiting_room=[0] * 1 + [1] * 3)
        ws.decomp_return_noncx(n=2)
        assert len([c for c in ws.waiting_room if c == 0]) == 0

    def test_total_card_count_preserved(self):
        ws = make_ws(deck=[0] * 10, waiting_room=[0] * 5 + [1] * 3)
        before = len(ws.deck) + len(ws.waiting_room)
        ws.decomp_return_noncx(n=2)
        after = len(ws.deck) + len(ws.waiting_room)
        assert before == after


class TestDecompReturnCx:
    def test_returns_n_cx_to_deck(self):
        ws = make_ws(deck=[0] * 10, waiting_room=[0] * 5 + [1] * 3)
        ws.decomp_return_cx(n=2)
        assert sum(ws.waiting_room) == 1  # CX3枚 → 2枚戻して1枚残る

    def test_fewer_cx_than_n_returns_all(self):
        # CX1枚しかないのにn=2 → 1枚だけ戻る
        ws = make_ws(deck=[0] * 10, waiting_room=[0] * 5 + [1] * 1)
        ws.decomp_return_cx(n=2)
        assert sum(ws.waiting_room) == 0

    def test_noncx_unchanged_in_waiting_room(self):
        ws = make_ws(deck=[0] * 10, waiting_room=[0] * 5 + [1] * 3)
        ws.decomp_return_cx(n=2)
        assert len([c for c in ws.waiting_room if c == 0]) == 5

    def test_total_card_count_preserved(self):
        ws = make_ws(deck=[0] * 10, waiting_room=[0] * 5 + [1] * 3)
        before = len(ws.deck) + len(ws.waiting_room)
        ws.decomp_return_cx(n=2)
        after = len(ws.deck) + len(ws.waiting_room)
        assert before == after
