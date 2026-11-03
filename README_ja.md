# Rinnai 乾太くん Home Assistant インテグレーション

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/miyagase/homeassistant-rinnai.svg)](https://github.com/miyagase/homeassistant-rinnai/releases)

Rinnai の乾太くん（ガス衣類乾燥機）を Home Assistant で監視するカスタムインテグレーションです。

## 機能

- 稼働状態のリアルタイム監視（60秒ポーリング）
- 乾燥コース・残り時間の取得
- トークン自動更新（期限切れ前後に自動でリフレッシュ）

## エンティティ

| エンティティ | 種別 | 説明 |
|---|---|---|
| `binary_sensor.kantakun_running` | Binary Sensor | 運転中かどうか |
| `sensor.kantakun_status` | Sensor | ステータス（停止中/運転中/待機中/エラー） |
| `sensor.kantakun_course` | Sensor | 乾燥コース |
| `sensor.kantakun_time_remaining` | Sensor | 残り時間（分） |

## 動作環境

- Home Assistant 2023.1.0 以降
- Rinnai 乾太くん（クラウド接続対応モデル）
- デバイスへのローカルネットワーク接続

## インストール

### HACS（推奨）

1. HACS → インテグレーション → ⋮ → カスタムリポジトリ
2. `https://github.com/miyagase/homeassistant-rinnai` を追加（カテゴリ: インテグレーション）
3. 「Rinnai 乾太くん」をインストール
4. HA を再起動

### 手動

`custom_components/rinnai/` を HA の `custom_components/` にコピーして再起動。

## セットアップ

設定 → デバイスとサービス → 統合を追加 → 「Rinnai」を検索

### ペアリング手順

1. 乾太くん本体で **L3 → OK** を操作する
2. HA のセットアップ画面で「**送信**」を押す
3. 本体に「OKボタンを押してください」と表示されたら、本体の **OK** を押す

自動でセットアップが完了します。スマートフォンアプリやパケットキャプチャは不要です。

## トークンについて

- アクセストークンの有効期限: 約24時間
- このインテグレーションは期限切れ2時間前（または期限切れ後）に自動でリフレッシュします
- リフレッシュトークンが失効した場合は再セットアップが必要です
