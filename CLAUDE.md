# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 開発フロー

- 機能追加・修正は必ず**新しいブランチを切って**作業する（`git checkout -b feature/xxx`）
- 作業完了後は**GitHubにプッシュしてPRを作成**する（`GITHUB_TOKEN` 環境変数を使いGitHub APIでPR作成可能）
- **マージはオーナー（wkonishi-sudo）が行う**。Claude Code側でmasterへの直接マージはしない
- マージ後はオーナーがブランチを削除し、Claude Codeは `git pull` でローカルを同期する

## 実行方法

```bash
python weiss_sim_GUI.py
```

依存ライブラリ: `matplotlib`, `tkinter`（標準ライブラリ）

## ファイル構成

```
weiss_sim_GUI.py      # 起動エントリーポイント（実行するファイル）
ws_sim/
├── __init__.py
├── game.py           # WeissSchwarz コアロジック
├── abilities.py      # 詰め能力 Mixin（touya/miku/michiru/song_for_all）
└── gui.py            # SimulatorGUI（UI層）
```

## アーキテクチャ概要

### `ws_sim/game.py` — WeissSchwarz クラス

デッキ・控え室・クロック・レベルの状態を保持し、ヴァイスシュヴァルツのダメージ解決ルールを実装する。`AbilityMixin` を継承して詰め能力を取り込む。

- **`damage(x)`**: x点ダメージを解決。キャンセル発生時はキャンセル以降のカードを山札先頭に戻す。リフレッシュ・レベルアップも内部で処理。
- **`refresh()`**: 山札が空になったとき、控え室をシャッフルして新しい山札を作り、先頭カードをクロックに乗せる。
- **`level_up()`**: クロックが7枚以上になったらレベルアップ（上7枚を控え室へ）。
- **`flip_trigger()`**: 攻撃側山札からトリガーを1枚めくる。ソウルトリガーなら1、それ以外は0を返し、山札状態を更新。
- **`attack(soul)`**: `flip_trigger()` の結果を加算して `damage()` を呼ぶ。トリガーありアタックに使用。
- **`simulate_attacks(attack_sequence)`**: 文字列のリストを受け取り順番に実行。数値文字列は `damage(x)`、`"Nt"` 形式（例: `3t`）は `attack(N)`、それ以外は関数名として解釈。

### `ws_sim/abilities.py` — AbilityMixin クラス

詰め能力を Mixin として定義。**新しい詰め能力を追加する場合はこのファイルだけ触ればよい。**

- **`touya(n, m)`**: 山下からn枚めくり、CX枚数×mダメージ。
- **`miku(n, m, k)`**: 山下からn枚めくり、CXが1枚以上あればk回mダメージ。
- **`michiru(n, m)`**: 山下からn枚めくり、CX枚数×mダメージを1回。
- **`song_for_all(n)`**: 山下からn枚公開してシャッフル、CX枚数分クロックに乗せる。

追加手順:
1. `AbilityMixin` にメソッドを追加（docstringにパラメータ説明を `パラメータ名: 説明` 形式で記載）
2. `get_special_attacks()` の返却リストに追加

### `ws_sim/gui.py` — SimulatorGUI クラス

tkinterのタブ構成で2つの画面を持つ。

- **単一シミュレーション タブ**: 指定した山札状態・行動列に対して10万回試行し、リーサル率と打点期待値を表示。
- **グラフ描画 タブ**: 山札枚数×CX枚数の全組み合わせについて1万回試行し、matplotlibでグラフ描画。別領域（手札・舞台など）のCX管理にも対応。
- **行動シーケンスの保存・読み込み**: 両タブで行動シーケンスをJSONファイルに保存・読み込み可能。
- **ソウルトリガー入力**: 攻撃側山札の状態（ソウルトリガー枚数/合計枚数）を入力し、トリガーありアタック（`Nt` 形式）でシミュレーションに反映。

## ゲームルールの重要な実装詳細

- デッキは `0`（非CX）と `1`（CX）の整数リストで表現。
- `is_dead()` はレベルリストが4以上で `True`（レベル4到達 = 死亡）。
- `damage_dealt` は `7 * len(self.level) + len(self.clock)` の初期値からの増分。
- グラフ描画時、山札全体のCX枚数は8枚固定前提（`8 - other_area_cx_count` を上限）。
- 攻撃側山札は `(atk_soul_triggers, atk_deck_size)` で管理。トリガーをめくるたびに状態が更新され、1回のシーケンス内で連動する。
- 行動シーケンスの `"Nt"` 形式（例: `3t`）はトリガーありアタックを表す。`"N"` 形式は固定ダメージ。
