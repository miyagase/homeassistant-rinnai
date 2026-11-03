# Rinnai 乾太くん Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

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

## インストール

### HACS（推奨）

1. HACS → カスタムリポジトリ → `https://github.com/iot-develop-ja/homeassistant-rinnai` を追加
2. 「Rinnai 乾太くん」をインストール
3. HA を再起動

### 手動

`custom_components/rinnai/` を HA の `custom_components/` にコピーして再起動。

## セットアップ

設定 → デバイスとサービス → 統合を追加 → 「Rinnai」を検索

以下の情報が必要です：

| 項目 | 取得方法 |
|---|---|
| コントローラーID | Rinnai アプリの通信をキャプチャして取得 |
| アクセストークン | 同上（`Authorization: Bearer` ヘッダー） |
| リフレッシュトークン | `POST /api/v2/users/refresh_token` レスポンスから取得 |

トークンの取得方法は [kantakun ディレクトリの README](https://github.com/iot-develop-ja/homeassistant-rinnai/blob/main/tools/README.md) を参照してください。

## トークンについて

- アクセストークンの有効期限: 約24時間
- このインテグレーションは期限切れ2時間前（または期限切れ後）に自動でリフレッシュします
- リフレッシュトークンが失効した場合は再セットアップが必要です
