# Asset License Management System

社内のソフトウェアライセンス、端末貸し出し、利用権限を統合管理するWebシステム

## 技術スタック

### バックエンド
- Django 4.2.7
- Django REST Framework 3.14.0
- PostgreSQL (psycopg 3.1.13)
- JWT認証 (djangorestframework-simplejwt)
- LDAP認証 (django-auth-ldap)

### フロントエンド (予定)
- React 18 + TypeScript
- Tailwind CSS
- React Query
- i18next (多言語対応)

### インフラ
- Docker + Docker Compose
- PostgreSQL 15
- Redis 7
- Nginx (本番環境)

## セットアップ

### 1. 環境構築

```bash
# リポジトリクローン
git clone <repository-url>
cd asset-license-management

# 仮想環境作成・有効化
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows

# 依存関係インストール
pip install -r requirements.txt
```

### 2. 環境変数設定

```bash
# .env.example をコピーして設定
cp .env.example .env
# .env ファイルを編集して適切な値を設定
```

### 3. Docker Compose でデータベース起動

```bash
# PostgreSQL と Redis を起動
docker-compose up -d db redis

# データベース接続確認
docker-compose exec db psql -U postgres -d asset_management_dev -c "SELECT version();"
```

### 4. Django セットアップ

```bash
# マイグレーション実行
python manage.py makemigrations
python manage.py migrate

# スーパーユーザー作成
python manage.py createsuperuser

# 開発サーバー起動
python manage.py runserver
```

## プロジェクト構造

```
asset_management/
├── asset_management/          # Django プロジェクト設定
│   ├── settings/             # 環境別設定ファイル
│   │   ├── base.py          # 基本設定
│   │   ├── development.py   # 開発環境設定
│   │   └── production.py    # 本番環境設定
│   ├── urls.py              # メインURL設定
│   └── wsgi.py              # WSGI設定
├── apps/                     # Django アプリケーション
│   ├── authentication/      # 認証機能
│   ├── employees/           # 社員管理
│   ├── devices/             # 端末管理
│   ├── licenses/            # ライセンス管理
│   ├── permissions/         # 権限管理
│   └── reports/             # レポート機能
├── common/                   # 共通ユーティリティ
│   ├── permissions.py       # カスタム権限
│   ├── pagination.py        # ページネーション
│   ├── exceptions.py        # カスタム例外
│   └── utils.py            # ユーティリティ関数
├── static/                   # 静的ファイル
├── media/                    # メディアファイル
├── logs/                     # ログファイル
├── requirements.txt          # Python依存関係
├── docker-compose.yml        # Docker Compose設定
├── Dockerfile               # Docker設定
└── README.md                # このファイル
```

## API エンドポイント

### 認証
- `POST /api/auth/login` - ログイン
- `POST /api/auth/logout` - ログアウト
- `GET /api/auth/me` - ユーザー情報取得

### 社員管理
- `GET /api/employees/` - 社員一覧
- `POST /api/employees/` - 社員登録
- `PUT /api/employees/{id}/` - 社員情報更新

### 端末管理
- `GET /api/devices/` - 端末一覧
- `POST /api/devices/` - 端末登録
- `POST /api/devices/{id}/assign/` - 端末割当

### ライセンス管理
- `GET /api/licenses/` - ライセンス一覧
- `POST /api/licenses/` - ライセンス登録
- `POST /api/licenses/{id}/assign/` - ライセンス割当

## 開発コマンド

```bash
# Django チェック
python manage.py check

# マイグレーション作成
python manage.py makemigrations

# マイグレーション実行
python manage.py migrate

# テスト実行
python manage.py test

# 静的ファイル収集
python manage.py collectstatic

# Django シェル
python manage.py shell
```

## Docker コマンド

```bash
# 全サービス起動
docker-compose up -d

# ログ確認
docker-compose logs -f web

# データベースシェル
docker-compose exec db psql -U postgres -d asset_management_dev

# コンテナ停止・削除
docker-compose down

# ボリューム含めて削除
docker-compose down -v
```

## 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `SECRET_KEY` | Django シークレットキー | - |
| `DEBUG` | デバッグモード | `False` |
| `DB_NAME` | データベース名 | `asset_management` |
| `DB_USER` | データベースユーザー | `postgres` |
| `DB_PASSWORD` | データベースパスワード | `postgres` |
| `DB_HOST` | データベースホスト | `localhost` |
| `DB_PORT` | データベースポート | `5432` |
| `LDAP_SERVER_URI` | LDAP サーバーURI | - |
| `CORS_ALLOWED_ORIGINS` | CORS許可オリジン | `http://localhost:3000` |

## ライセンス

このプロジェクトは社内利用のため、ライセンスは適用されません。