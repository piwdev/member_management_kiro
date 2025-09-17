# Design Document

## Overview

新規ユーザー登録機能は、既存の認証システムに統合される形で実装される。Django REST Frameworkベースのバックエンドと、React TypeScriptベースのフロントエンドで構成される。セキュリティを重視し、既存のユーザーモデルとの整合性を保ちながら、直感的なユーザーインターフェースを提供する。

## Architecture

### Backend Architecture

```
apps/authentication/
├── views.py (新規登録ビューを追加)
├── serializers.py (登録用シリアライザーを追加)
├── urls.py (登録エンドポイントを追加)
├── models.py (既存のUserモデルを活用)
└── validators.py (新規作成: カスタムバリデーター)
```

### Frontend Architecture

```
frontend/src/
├── components/auth/
│   ├── LoginForm.tsx (既存)
│   └── RegisterForm.tsx (新規作成)
├── contexts/AuthContext.tsx (register関数を追加)
├── i18n/locales/
│   ├── ja.json (登録関連の翻訳を追加)
│   └── en.json (登録関連の翻訳を追加)
└── types/index.ts (登録関連の型定義を追加)
```

### API Design

**POST /auth/register/**
- 新規ユーザー登録エンドポイント
- リクエスト: ユーザー情報（username, email, password, confirm_password, first_name, last_name, department, position, location, employee_id）
- レスポンス: 作成されたユーザー情報（パスワードは除く）
- エラーハンドリング: バリデーションエラー、重複エラー

## Components and Interfaces

### Backend Components

#### 1. UserRegistrationSerializer
```python
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'employee_id', 
            'department', 'position', 'location'
        ]
    
    def validate(self, attrs):
        # パスワード一致確認
        # ユーザー名・メール重複確認
        # 社員ID重複確認（入力された場合）
        
    def create(self, validated_data):
        # パスワードハッシュ化
        # ユーザー作成
        # 登録ログ記録
```

#### 2. UserRegistrationView
```python
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_view(request):
    # レート制限チェック
    # データバリデーション
    # ユーザー作成
    # 成功レスポンス返却
```

#### 3. Custom Validators
```python
def validate_password_strength(password):
    # パスワード強度チェック
    # 最低8文字、英数字含有など

def validate_employee_id_format(employee_id):
    # 社員ID形式チェック（設定された場合）
```

### Frontend Components

#### 1. RegisterForm Component
```typescript
interface RegisterFormData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
  department: string;
  position: string;
  location: string;
  employeeId?: string;
}

const RegisterForm: React.FC = () => {
  // フォーム状態管理
  // バリデーション
  // 送信処理
  // エラーハンドリング
  // 成功時のリダイレクト
}
```

#### 2. AuthContext Extension
```typescript
interface AuthContextType {
  // 既存のプロパティ
  register: (userData: RegisterFormData) => Promise<void>;
}
```

## Data Models

### User Model (既存を活用)
```python
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=10, choices=LOCATION_CHOICES, blank=True)
    # その他既存フィールド
```

### Registration Attempt Model (新規作成)
```python
class RegistrationAttempt(models.Model):
    username = models.CharField(max_length=150)
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    created_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
```

## Error Handling

### Backend Error Responses
```json
{
  "error": "validation_error",
  "details": {
    "username": ["このユーザー名は既に使用されています。"],
    "email": ["このメールアドレスは既に登録されています。"],
    "password": ["パスワードは8文字以上である必要があります。"],
    "confirm_password": ["パスワードが一致しません。"]
  }
}
```

### Frontend Error Handling
- フィールドレベルのリアルタイムバリデーション
- サーバーエラーの適切な表示
- ネットワークエラーのハンドリング
- ユーザーフレンドリーなエラーメッセージ

### Rate Limiting
- IP単位での登録試行制限（1時間に5回まで）
- 同一メールアドレスでの登録試行制限
- Django-ratelimitを使用した実装

## Testing Strategy

### Backend Testing
```python
class UserRegistrationTests(TestCase):
    def test_successful_registration(self):
        # 正常な登録フローのテスト
        
    def test_duplicate_username_error(self):
        # ユーザー名重複エラーのテスト
        
    def test_duplicate_email_error(self):
        # メールアドレス重複エラーのテスト
        
    def test_password_validation(self):
        # パスワードバリデーションのテスト
        
    def test_rate_limiting(self):
        # レート制限のテスト
```

### Frontend Testing
```typescript
describe('RegisterForm', () => {
  test('renders registration form correctly', () => {
    // フォーム表示のテスト
  });
  
  test('validates required fields', () => {
    // 必須フィールドバリデーションのテスト
  });
  
  test('handles successful registration', () => {
    // 成功時の処理テスト
  });
  
  test('displays server errors correctly', () => {
    // サーバーエラー表示のテスト
  });
});
```

### Integration Testing
- E2Eテストでの登録フロー全体のテスト
- 登録後のログイン機能との連携テスト
- 多言語対応のテスト

## Security Considerations

### Input Validation
- すべての入力フィールドでサーバーサイドバリデーション
- SQLインジェクション対策
- XSS対策（入力値のサニタイズ）

### Password Security
- bcryptによるパスワードハッシュ化
- パスワード強度要件の実装
- パスワード履歴の管理（将来的な拡張）

### CSRF Protection
- Django標準のCSRF保護機能を活用
- APIトークンベースの認証

### Rate Limiting
- 登録試行回数の制限
- IP単位での制限
- 異常な登録パターンの検出

## Internationalization

### 日本語対応
```json
{
  "auth": {
    "register": "新規登録",
    "firstName": "名",
    "lastName": "姓",
    "confirmPassword": "パスワード確認",
    "employeeId": "社員ID",
    "registrationSuccess": "登録が完了しました。ログインしてください。",
    "registrationFailed": "登録に失敗しました。",
    "validation": {
      "usernameRequired": "ユーザー名は必須です",
      "emailRequired": "メールアドレスは必須です",
      "passwordTooShort": "パスワードは8文字以上である必要があります",
      "passwordMismatch": "パスワードが一致しません",
      "usernameExists": "このユーザー名は既に使用されています",
      "emailExists": "このメールアドレスは既に登録されています"
    }
  }
}
```

### 英語対応
```json
{
  "auth": {
    "register": "Register",
    "firstName": "First Name",
    "lastName": "Last Name",
    "confirmPassword": "Confirm Password",
    "employeeId": "Employee ID",
    "registrationSuccess": "Registration completed. Please log in.",
    "registrationFailed": "Registration failed.",
    "validation": {
      "usernameRequired": "Username is required",
      "emailRequired": "Email address is required",
      "passwordTooShort": "Password must be at least 8 characters",
      "passwordMismatch": "Passwords do not match",
      "usernameExists": "This username is already taken",
      "emailExists": "This email address is already registered"
    }
  }
}
```

## Performance Considerations

### Database Optimization
- ユーザー名とメールアドレスのインデックス最適化
- 登録試行履歴の定期的なクリーンアップ

### Frontend Optimization
- フォームバリデーションのデバウンス処理
- 不要な再レンダリングの防止
- 適切なローディング状態の表示

### Caching Strategy
- 登録フォームの静的リソースキャッシュ
- API レスポンスの適切なキャッシュヘッダー設定

## Monitoring and Logging

### Registration Metrics
- 登録成功率の監視
- 登録失敗の原因分析
- 登録フローの離脱率分析

### Security Monitoring
- 異常な登録パターンの検出
- レート制限の発動状況
- 不正な登録試行の監視

### Error Tracking
- 登録エラーの詳細ログ
- フロントエンドエラーの収集
- パフォーマンス指標の監視