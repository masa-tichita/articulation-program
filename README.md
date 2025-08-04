# articulation-program
2025年度 高大連携 日立北1,2班 最適化アプリケーション

## 🎯 使用技術
- **PuLP**: 数理最適化モデラー
- **Streamlit**: インタラクティブなWebインターフェース
- **Pydantic v2**: 型安全性の担保
- **loguru**: 詳細なログ記録

## 🏗️ プロジェクト構造

```
articulation-program/
├── src/
│   ├── main.py                        # メイン
│   ├── apps/
│   │   └── opt-apps-layout.py         # スマホアプリ配置最適化のバックエンド
│   ├── modules/
│   │   ├── const.py                  # 様々なオブジェクトに対する型定義
│   ├── pages/
│   │   └── app_view_opt.py           # スマホアプリ配置最適化のフロント
│   └── utils/
│       ├── logging.py                # ログ設定
│       ├── system.py                 # システムユーティリティ(timer, path)
├── pyproject.toml                    # 依存関係管理
├── uv.lock                          # ロックファイル
├── README.md                        # このファイル
```

## 🚀 インストールと起動

### 使用環境・ライブラリ

- Python環境：Python 3.13以上
- [uv](https://docs.astral.sh/uv/) : パッケージマネージャ
- [Poe the Poet](https://poethepoet.natn.io/index.html) : タスクランナー

### インストールと環境設定

```bash
# リポジトリをクローン
git clone <repository-url>
cd articulation-program

# 依存関係をインストール
uv sync
# ターミナルへの仮想環境の適用
source .venv/bin/activate
```

### 起動方法

```bash
# Streamlitアプリケーションの起動
# uvがすでにターミナルで起動している場合は、`uv run` は不要
(uv run) poe start
```

アプリケーションが起動すると、ブラウザで `http://localhost:8501` にアクセスできます。

## 開発
- フォーマッター(ruff)
```bash
# uvがすでにターミナルで起動している場合は、`uv run` は不要
(uv run) poe fmt
```
- リンター(pyright)
```bash
# uvがすでにターミナルで起動している場合は、`uv run` は不要
(uv run) poe lint
```