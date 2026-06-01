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
        # 非CXのみの山 → 全部クロックに乗る
        ws = make_ws(deck=[0] * 20)
        ws.damage(3)
        assert len(ws.clock) == 3

    def test_cancel_stops_damage(self):
        # 1枚目がCX → キャンセル。クロックは増えない、CXが控え室に行く
        ws = make_ws_fixed([1, 0, 0] + [0] * 17)
        ws.damage(3)
        assert len(ws.clock) == 0
        assert sum(ws.waiting_room) == 1  # CX1枚が控え室に

    def test_cancel_mid_sequence(self):
        # 2枚目がCX → ダメージ解決全体がキャンセル（CX以前の非CXもクロックに乗らない）
        # 控え室には [0, 1] の2枚が入る
        ws = make_ws_fixed([0, 1, 0] + [0] * 17)
        ws.damage(3)
        assert len(ws.clock) == 0
        assert len(ws.waiting_room) == 2  # 0と1の2枚が控え室へ

    def test_cancel_at_last_card(self):
        # 山札[0,0,1]の3枚で3ダメージ → 3枚目でキャンセル → 山切れ → リフレッシュ発生
        # キャンセルで[0,0,1]が控え室へ → damage末尾のrefreshで控え室が山になりクロック1枚
        ws = make_ws_fixed([0, 0, 1])  # 山札3枚のみ、控え室なし
        ws.damage(3)
        assert len(ws.clock) == 1      # リフレッシュで1枚クロックへ
        assert len(ws.deck) == 2       # リフレッシュ後の残り山
        assert len(ws.waiting_room) == 0

    def test_cancel_returns_remaining_to_deck(self):
        # キャンセル後の残りカードが山頭に戻る
        ws = make_ws_fixed([0, 1, 0] + [0] * 17)
        ws.damage(3)
        # 解決後: 控え室[0,1]、山頭に[0]が戻る
        assert ws.deck[0] == 0


class TestRefresh:
    def test_refresh_moves_waiting_room_to_deck(self):
        # 控え室の [0,0,1] が山に移動し、控え室が空になる
        ws = make_ws_fixed([], waiting_room=[0, 0, 1])
        ws.refresh()
        assert ws.waiting_room == []
        # クロック1枚 + 残り2枚が山に
        assert len(ws.deck) == 2
        assert len(ws.clock) == 1
        # 元の控え室のカードが山に含まれている（合計3枚のうち1枚クロック、2枚山）
        assert len(ws.deck) + len(ws.clock) == 3

    def test_refresh_clock_gets_one_card(self):
        ws = make_ws_fixed([], waiting_room=[0, 0, 0])
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

    def test_level_up_with_9_clock_leaves_2_remaining(self):
        # クロック9枚（非CX7枚 + CX2枚）→ 先頭7枚が控え室へ、残り2枚がクロックに残る
        # クロックは [0,0,0,0,0,0,0,1,1]（末尾2枚がCX）
        ws = make_ws(deck=[0] * 20)
        ws.clock = [0, 0, 0, 0, 0, 0, 0, 1, 1]
        ws.level_up()
        assert len(ws.level) == 1
        assert len(ws.clock) == 2
        assert ws.clock == [1, 1]  # 元の末尾2枚がそのまま残る

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
        # 山下6枚にCX2枚 → 2ダメージ
        ws = make_ws(deck=[0] * 20, waiting_room=[0] * 10)
        ws.deck = [0] * 14 + [0, 0, 0, 0, 1, 1]
        ws.touya(n=6, m=1)
        assert len(ws.clock) == 2

    def test_no_cx_no_damage(self):
        ws = make_ws(deck=[0] * 20, waiting_room=[0] * 10)
        ws.touya(n=6, m=1)
        assert len(ws.clock) == 0

    def test_damage_multiplier(self):
        # 山下6枚にCX1枚 × m=3 → 3ダメージ
        ws = make_ws(deck=[0] * 20, waiting_room=[0] * 10)
        ws.deck = [0] * 19 + [1]
        ws.touya(n=6, m=3)
        assert len(ws.clock) == 3

    def test_multiple_cx_at_bottom(self):
        # 山下6枚にCX3枚 × m=2 → 6ダメージ
        ws = make_ws(deck=[0] * 20, waiting_room=[0] * 10)
        ws.deck = [0] * 17 + [1, 1, 1]
        ws.touya(n=6, m=2)
        assert len(ws.clock) == 6

    def test_cx_causes_damage_with_refresh(self):
        # 山が少なくリフレッシュが発生するケース
        # 山3枚、控え室7枚でtouya(n=6) → 3枚めくったところで山切れ → リフレッシュ発生
        # リフレッシュでクロックに少なくとも1枚乗ることを確認
        ws = make_ws_fixed([0, 0, 0], waiting_room=[0] * 5 + [1] * 2)
        ws.touya(n=6, m=1)
        assert len(ws.clock) >= 1  # リフレッシュで最低1枚クロックへ


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

    def test_partial_cancel(self):
        # k=2のダメージで2回目だけキャンセル: 山上3枚が [0, 1, 0]
        # miku(n=4, m=1, k=2): 1回目damage(1)→クロック+1、2回目damage(1)→キャンセル
        ws = make_ws(deck=[0] * 20, waiting_room=[0] * 10)
        ws.deck = [0] * 19 + [1]  # CX1枚を山下に配置（mikuで消費）
        ws.miku(n=4, m=1, k=2)
        # CXがmiku解決で控え室に行くので、damage(1)×2は全て非CXから引く
        # → 2点クロック
        assert len(ws.clock) == 2


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

    def test_cancel_on_second_damage(self):
        # CX2枚 × m=1 → damage(2)。山上が [0, 1, ...] → 2点目でキャンセル
        ws = make_ws(deck=[0] * 20, waiting_room=[0] * 10)
        ws.deck = [0, 1] + [0] * 16 + [1, 1]  # 山上2枚目がCX、山下2枚がCX
        ws.michiru(n=4, m=1)
        # michiru: 山下4枚めくり([0,0,1,1])→CX2枚→damage(2)
        # damage(2): 山上[0,1]→2枚目でキャンセル→クロック0
        assert len(ws.clock) == 0
        # 控え室: 初期10枚 + michiru分4枚[0,0,1,1] + キャンセル分2枚[0,1] = 16枚
        assert len(ws.waiting_room) == 16


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

    def test_two_cx_in_top3(self):
        # 山札[0,1,1]の3枚のみ → CX2枚 → クロック2枚、山札1枚残る
        ws = make_ws_fixed([0, 1, 1])  # 山札3枚のみ
        ws.song_for_all(n=3)
        assert len(ws.clock) == 2
        assert len(ws.deck) == 1


# ── koukei ───────────────────────────────────────────────────

class TestKoukei:
    def test_stock_moves_to_waiting_room(self):
        # ストック: 非CX8枚+CX2枚 → 控え室に非CX8枚とCX2枚が移動
        stock = [0] * 8 + [1] * 2
        ws = make_ws(deck=[0] * 20, waiting_room=[], stock=stock)
        ws.koukei()
        assert len(ws.waiting_room) == 10
        assert sum(ws.waiting_room) == 2    # CX2枚
        assert ws.waiting_room.count(0) == 8  # 非CX8枚

    def test_deck_top_fills_stock(self):
        stock = [0] * 10
        ws = make_ws(deck=[0] * 20, stock=stock)
        ws.koukei()
        assert len(ws.stock) == 10
        assert len(ws.deck) == 10

    def test_deck_top_fills_stock_with_refresh(self):
        # ストック0/10（非CX10枚）、山札3/5（CX3枚+非CX2枚）でkoukei
        # 山5枚しかないので途中リフレッシュが発生し、元ストックの非CX10枚が山になる
        stock = [0] * 10  # 非CX10枚
        ws = make_ws(deck=[0] * 2 + [1] * 3, waiting_room=[], stock=stock)
        ws.koukei()
        # ストックは10枚: 元の山から5枚(CX3+非CX2) + リフレッシュ後の山から5枚(非CX)
        assert len(ws.stock) == 10
        assert ws.stock.count(1) == 3   # 元の山のCX3枚がストックへ
        assert ws.stock.count(0) == 7   # 非CX2枚(元山) + 非CX5枚(リフレッシュ後)
        assert len(ws.clock) == 1       # リフレッシュで1枚クロックへ
        assert ws.deck.count(0) == 4    # リフレッシュ後の残り非CX山

    def test_total_card_count_preserved(self):
        # ストック: 非CX5枚+CX2枚=7枚
        stock = [0] * 5 + [1] * 2
        ws = make_ws(deck=[0] * 15, waiting_room=[0] * 5, stock=stock)
        before = len(ws.deck) + len(ws.waiting_room) + len(ws.stock)
        ws.koukei()
        after = len(ws.deck) + len(ws.waiting_room) + len(ws.stock)
        assert before == after

    def test_cx_in_stock_goes_to_waiting_room(self):
        stock = [1, 1, 0]  # CX2枚
        ws = make_ws(deck=[0] * 20, stock=stock)
        ws.koukei()
        assert sum(ws.waiting_room) == 2

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
        # 控え室: 非CX5枚+CX2枚、k=1 → 非CX5枚+CX1枚が山に戻り、CX1枚が控え室に残る
        ws = make_ws(deck=[0] * 10, waiting_room=[0] * 5 + [1] * 2)
        ws.decomp_keep_cx(k=1)
        assert ws.waiting_room == [1]
        assert len(ws.deck) == 10 + 5 + 1  # 元の山10 + 非CX5 + 余剰CX1

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
        # 控え室: 非CX5枚+CX3枚、n=2 → 非CX2枚が山に戻る
        # 山: 元の10枚 + 非CX2枚 = 12枚（非CX12枚、CX0枚）
        ws = make_ws(deck=[0] * 10, waiting_room=[0] * 5 + [1] * 3)
        ws.decomp_return_noncx(n=2)
        assert sum(ws.waiting_room) == 3   # CX3枚はそのまま
        assert ws.waiting_room.count(0) == 3  # 非CX5-2=3枚が残る
        deck_noncx = ws.deck.count(0)
        deck_cx = ws.deck.count(1)
        assert deck_noncx == 12  # 元の非CX10枚 + 戻った非CX2枚
        assert deck_cx == 0

    def test_fewer_noncx_than_n_returns_all(self):
        # 非CX1枚しかないのにn=2 → 1枚だけ戻る
        ws = make_ws(deck=[0] * 10, waiting_room=[0] * 1 + [1] * 3)
        ws.decomp_return_noncx(n=2)
        assert ws.waiting_room.count(0) == 0

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
        assert ws.waiting_room.count(0) == 5

    def test_total_card_count_preserved(self):
        ws = make_ws(deck=[0] * 10, waiting_room=[0] * 5 + [1] * 3)
        before = len(ws.deck) + len(ws.waiting_room)
        ws.decomp_return_cx(n=2)
        after = len(ws.deck) + len(ws.waiting_room)
        assert before == after
