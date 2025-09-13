# 設計文書

## 概要

社内のソフトウェアライセンス・端末・権限管理システムは、Webベースのフルスタックアプリケーションとして設計します。日本語UIを基本とし、多国籍社員に対応するため英語切り替えも提供します。東京・沖縄の2拠点とリモートワークに対応した統合管理システムです。

## アーキテクチャ

### システム構成

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   フロントエンド   │    │   バックエンド    │    │   データベース    │
│                 │    │                 │    │                 │
│   React + TS    │◄──►│ Django + Python  │◄──►│   PostgreSQL    │
│   Tailwind CSS  │    │ Django REST API  │    │                 │
│   React Query   │    │   Django ORM     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   認証システム    │
                       │                 │
                       │  LDAP/AD連携    │
                       │   JWT Token     │
                       └─────────────────┘
```

### 技術スタック

**フロントエンド:**
- React 18 + TypeScript
- Tailwind CSS (レスポンシブデザイン)
- React Query (サーバー状態管理)
- React Hook Form (フォーム管理)
- React Router (ルーティング)
- i18next (多言語対応)

**バックエンド:**
- Django 4.2+ + Python 3.11+
- Django REST Framework (API構築)
- Django ORM (データベースアクセス)
- JWT (認証トークン) - djangorestframework-simplejwt
- django-auth-ldap (LDAP認証)
- django-cors-headers (CORS対応)

**データベース:**
- PostgreSQL 15+
- Redis (セッション・キャッシュ)

**インフラ:**
- Docker + Docker Compose (開発環境)
- Nginx (リバースプロキシ)

## コンポーネントと インターフェース

### フロントエンドコンポーネント構成

```
src/
├── components/
│   ├── common/           # 共通コンポーネント
│   │   ├── Layout.tsx
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── LanguageSwitch.tsx
│   ├── employees/        # 社員管理
│   │   ├── EmployeeList.tsx
│   │   ├── EmployeeForm.tsx
│   │   └── EmployeeDetail.tsx
│   ├── devices/          # 端末管理
│   │   ├── DeviceList.tsx
│   │   ├── DeviceForm.tsx
│   │   └── DeviceAssignment.tsx
│   ├── licenses/         # ライセンス管理
│   │   ├── LicenseList.tsx
│   │   ├── LicenseForm.tsx
│   │   └── LicenseAssignment.tsx
│   ├── permissions/      # 権限管理
│   │   ├── RoleManagement.tsx
│   │   └── PolicyEditor.tsx
│   ├── reports/          # レポート
│   │   ├── UsageReport.tsx
│   │   ├── CostAnalysis.tsx
│   │   └── InventoryReport.tsx
│   └── dashboard/        # ダッシュボード
│       ├── AdminDashboard.tsx
│       └── UserDashboard.tsx
├── hooks/                # カスタムフック
├── services/             # API通信
├── types/                # TypeScript型定義
└── utils/                # ユーティリティ
```

### バックエンドAPI構成

```
asset_management/         # Djangoプロジェクト
├── settings/
│   ├── __init__.py
│   ├── base.py          # 基本設定
│   ├── development.py   # 開発環境設定
│   └── production.py    # 本番環境設定
├── urls.py              # メインURL設定
└── wsgi.py

apps/                    # Djangoアプリケーション
├── authentication/      # 認証アプリ
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── employees/           # 社員管理アプリ
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── devices/             # 端末管理アプリ
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── licenses/            # ライセンス管理アプリ
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── permissions/         # 権限管理アプリ
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
└── reports/             # レポートアプリ
    ├── models.py
    ├── views.py
    ├── serializers.py
    └── urls.py

common/                  # 共通ユーティリティ
├── permissions.py       # カスタム権限
├── pagination.py        # ページネーション
├── exceptions.py        # カスタム例外
└── utils.py            # ユーティリティ関数
```

### API エンドポイント設計

**認証:**
- `POST /api/auth/login` - ログイン
- `POST /api/auth/logout` - ログアウト
- `GET /api/auth/me` - ユーザー情報取得

**社員管理:**
- `GET /api/employees` - 社員一覧取得
- `POST /api/employees` - 社員登録
- `PUT /api/employees/:id` - 社員情報更新
- `DELETE /api/employees/:id` - 社員削除

**端末管理:**
- `GET /api/devices` - 端末一覧取得
- `POST /api/devices` - 端末登録
- `PUT /api/devices/:id` - 端末情報更新
- `POST /api/devices/:id/assign` - 端末割当
- `POST /api/devices/:id/return` - 端末返却

**ライセンス管理:**
- `GET /api/licenses` - ライセンス一覧取得
- `POST /api/licenses` - ライセンス登録
- `PUT /api/licenses/:id` - ライセンス情報更新
- `POST /api/licenses/:id/assign` - ライセンス割当
- `DELETE /api/licenses/:id/assign/:employeeId` - ライセンス割当解除

**レポート:**
- `GET /api/reports/usage` - 利用状況レポート
- `GET /api/reports/cost` - コスト分析レポート
- `GET /api/reports/inventory` - 在庫レポート

## データモデル

### 主要エンティティ

```typescript
// 社員
interface Employee {
  id: string
  employeeId: string        // 社員ID
  name: string             // 氏名
  email: string            // メールアドレス
  department: string       // 部署
  position: string         // 役職
  location: 'TOKYO' | 'OKINAWA' | 'REMOTE'  // 勤務地
  hireDate: Date          // 入社日
  status: 'ACTIVE' | 'INACTIVE'  // ステータス
  createdAt: Date
  updatedAt: Date
}

// 端末
interface Device {
  id: string
  type: 'LAPTOP' | 'DESKTOP' | 'TABLET' | 'SMARTPHONE'  // 端末種別
  manufacturer: string     // メーカー
  model: string           // モデル
  serialNumber: string    // シリアル番号
  purchaseDate: Date      // 購入日
  warrantyExpiry: Date    // 保証期限
  status: 'AVAILABLE' | 'ASSIGNED' | 'MAINTENANCE' | 'DISPOSED'  // ステータス
  createdAt: Date
  updatedAt: Date
}

// ソフトウェアライセンス
interface License {
  id: string
  softwareName: string    // ソフトウェア名
  licenseType: string     // ライセンス種別
  totalCount: number      // 購入数
  availableCount: number  // 利用可能数
  expiryDate: Date       // 有効期限
  licenseKey?: string    // ライセンスキー
  pricingModel: 'MONTHLY' | 'YEARLY' | 'PERPETUAL'  // 課金体系
  unitPrice: number      // 単価
  createdAt: Date
  updatedAt: Date
}

// 端末割当
interface DeviceAssignment {
  id: string
  deviceId: string
  employeeId: string
  assignedDate: Date     // 割当日
  returnDate?: Date      // 返却日
  purpose: string        // 使用目的
  status: 'ACTIVE' | 'RETURNED'
}

// ライセンス割当
interface LicenseAssignment {
  id: string
  licenseId: string
  employeeId: string
  assignedDate: Date     // 割当日
  startDate: Date        // 利用開始日
  endDate?: Date         // 利用終了日
  purpose: string        // 利用目的
  status: 'ACTIVE' | 'EXPIRED' | 'REVOKED'
}

// 権限ポリシー
interface PermissionPolicy {
  id: string
  name: string           // ポリシー名
  department?: string    // 対象部署
  position?: string      // 対象役職
  allowedDeviceTypes: string[]     // 許可端末種別
  allowedSoftware: string[]        // 許可ソフトウェア
  restrictedSoftware: string[]     // 禁止ソフトウェア
  createdAt: Date
  updatedAt: Date
}
```

### データベーススキーマ (Django Models)

```python
# employees/models.py
class Employee(models.Model):
    LOCATION_CHOICES = [
        ('TOKYO', '東京'),
        ('OKINAWA', '沖縄'),
        ('REMOTE', 'リモート'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'アクティブ'),
        ('INACTIVE', '非アクティブ'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    employee_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    location = models.CharField(max_length=10, choices=LOCATION_CHOICES)
    hire_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'employees'

# devices/models.py
class Device(models.Model):
    TYPE_CHOICES = [
        ('LAPTOP', 'ラップトップ'),
        ('DESKTOP', 'デスクトップ'),
        ('TABLET', 'タブレット'),
        ('SMARTPHONE', 'スマートフォン'),
    ]
    
    STATUS_CHOICES = [
        ('AVAILABLE', '利用可能'),
        ('ASSIGNED', '貸出中'),
        ('MAINTENANCE', '修理中'),
        ('DISPOSED', '廃棄'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True)
    purchase_date = models.DateField()
    warranty_expiry = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'devices'

# licenses/models.py
class License(models.Model):
    PRICING_CHOICES = [
        ('MONTHLY', '月額'),
        ('YEARLY', '年額'),
        ('PERPETUAL', '買い切り'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    software_name = models.CharField(max_length=200)
    license_type = models.CharField(max_length=100)
    total_count = models.PositiveIntegerField()
    available_count = models.PositiveIntegerField()
    expiry_date = models.DateField()
    license_key = models.TextField(blank=True, null=True)
    pricing_model = models.CharField(max_length=20, choices=PRICING_CHOICES)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'licenses'
```

## エラーハンドリング

### エラー分類と対応

**認証エラー:**
- 401 Unauthorized: ログイン必須
- 403 Forbidden: 権限不足
- 対応: ログイン画面へリダイレクト、権限エラーメッセージ表示

**バリデーションエラー:**
- 400 Bad Request: 入力値不正
- 対応: フィールド別エラーメッセージ表示

**ビジネスロジックエラー:**
- 409 Conflict: ライセンス不足、端末重複割当等
- 対応: 具体的なエラーメッセージと解決方法の提示

**システムエラー:**
- 500 Internal Server Error: サーバーエラー
- 対応: エラーログ記録、ユーザーには汎用エラーメッセージ

### エラーレスポンス形式

```typescript
interface ErrorResponse {
  error: {
    code: string
    message: string
    details?: Record<string, string[]>  // フィールド別エラー
  }
}
```

## テスト戦略

### テスト構成

**ユニットテスト:**
- Jest + Testing Library (フロントエンド)
- Jest + Supertest (バックエンド)
- カバレッジ目標: 80%以上

**統合テスト:**
- Django REST Framework APIテスト
- Django TestCase (データベース操作テスト)
- 認証フローテスト

**E2Eテスト:**
- Playwright
- 主要ユーザーフロー
- 多言語切り替えテスト

### テストデータ

**開発環境:**
- Docker Compose でテスト用PostgreSQL起動
- Django Fixtures でマスターデータ投入
- Django Management Command でテストデータ作成
- テストユーザー、サンプルデバイス・ライセンス作成

**テストシナリオ:**
1. 管理者ログイン → 社員登録 → 端末割当 → レポート確認
2. 社員ログイン → 自分のリソース確認 → 新規申請
3. 権限変更 → アクセス制御確認
4. ライセンス期限切れ → 通知確認
5. 多言語切り替え → UI表示確認