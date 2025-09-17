"""
Custom validators for user registration.
"""

import re
import html
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext as _


def validate_password_strength(password):
    """
    パスワード強度をチェックする関数
    
    Requirements:
    - 最低8文字以上
    - 英数字を含む
    - 特殊文字を含む（推奨）
    """
    if len(password) < 8:
        raise ValidationError(
            _('パスワードは8文字以上である必要があります。'),
            code='password_too_short'
        )
    
    # 英字チェック
    if not re.search(r'[a-zA-Z]', password):
        raise ValidationError(
            _('パスワードには英字を含める必要があります。'),
            code='password_no_letter'
        )
    
    # 数字チェック
    if not re.search(r'\d', password):
        raise ValidationError(
            _('パスワードには数字を含める必要があります。'),
            code='password_no_number'
        )
    
    # Django標準のパスワードバリデーションも実行
    try:
        validate_password(password)
    except ValidationError as e:
        # Django標準のエラーメッセージを日本語に変換
        error_messages = []
        for error in e.error_list:
            if 'too common' in str(error):
                error_messages.append('このパスワードは一般的すぎます。')
            elif 'too similar' in str(error):
                error_messages.append('パスワードがユーザー情報と似すぎています。')
            elif 'entirely numeric' in str(error):
                error_messages.append('パスワードは数字のみにできません。')
            else:
                error_messages.append(str(error))
        
        if error_messages:
            raise ValidationError(error_messages, code='password_validation_failed')


def validate_employee_id_format(employee_id):
    """
    社員ID形式をバリデーションする関数
    
    Format: 英数字、ハイフン、アンダースコアのみ許可
    Length: 3-20文字
    """
    if not employee_id:
        return  # 空の場合はスキップ（任意フィールド）
    
    if len(employee_id) < 3:
        raise ValidationError(
            _('社員IDは3文字以上である必要があります。'),
            code='employee_id_too_short'
        )
    
    if len(employee_id) > 20:
        raise ValidationError(
            _('社員IDは20文字以下である必要があります。'),
            code='employee_id_too_long'
        )
    
    # 英数字、ハイフン、アンダースコアのみ許可
    if not re.match(r'^[a-zA-Z0-9_-]+$', employee_id):
        raise ValidationError(
            _('社員IDには英数字、ハイフン、アンダースコアのみ使用できます。'),
            code='employee_id_invalid_format'
        )


def validate_username_format(username):
    """
    ユーザー名形式をバリデーションする関数
    
    Requirements:
    - 3-150文字
    - 英数字、アンダースコア、ハイフンのみ
    - 先頭は英字または数字
    """
    if len(username) < 3:
        raise ValidationError(
            _('ユーザー名は3文字以上である必要があります。'),
            code='username_too_short'
        )
    
    if len(username) > 150:
        raise ValidationError(
            _('ユーザー名は150文字以下である必要があります。'),
            code='username_too_long'
        )
    
    # 英数字、アンダースコア、ハイフンのみ許可
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        raise ValidationError(
            _('ユーザー名には英数字、アンダースコア、ハイフンのみ使用できます。'),
            code='username_invalid_format'
        )
    
    # 先頭は英字または数字
    if not re.match(r'^[a-zA-Z0-9]', username):
        raise ValidationError(
            _('ユーザー名は英字または数字で始まる必要があります。'),
            code='username_invalid_start'
        )


def validate_name_format(name, field_name='名前'):
    """
    名前フィールドの形式をバリデーションする関数
    
    Requirements:
    - 1-50文字
    - 特殊文字の制限
    """
    if not name:
        return  # 空の場合はスキップ
    
    if len(name) > 50:
        raise ValidationError(
            _(f'{field_name}は50文字以下である必要があります。'),
            code='name_too_long'
        )
    
    # 制御文字をチェック
    if any(ord(char) < 32 for char in name):
        raise ValidationError(
            _(f'{field_name}に無効な文字が含まれています。'),
            code='name_invalid_character'
        )


def validate_department_position_format(value, field_name):
    """
    部署・役職フィールドの形式をバリデーションする関数
    
    Requirements:
    - 100文字以下
    - 制御文字の禁止
    """
    if not value:
        return  # 空の場合はスキップ
    
    if len(value) > 100:
        raise ValidationError(
            _(f'{field_name}は100文字以下である必要があります。'),
            code='field_too_long'
        )
    
    # 制御文字をチェック
    if any(ord(char) < 32 for char in value):
        raise ValidationError(
            _(f'{field_name}に無効な文字が含まれています。'),
            code='field_invalid_character'
        )


def sanitize_input(value):
    """
    入力値をサニタイズする関数（XSS対策）
    
    - HTMLエスケープ
    - 制御文字の除去
    - 前後の空白除去
    """
    if not value:
        return value
    
    # 文字列に変換
    value = str(value)
    
    # HTMLエスケープ
    value = html.escape(value)
    
    # 制御文字を除去（改行・タブは保持）
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\t')
    
    # 前後の空白を除去
    value = value.strip()
    
    return value


def validate_no_sql_injection(value):
    """
    SQLインジェクション攻撃パターンをチェックする関数
    """
    if not value:
        return
    
    # 危険なSQLキーワードパターン
    sql_patterns = [
        r'\bunion\b.*\bselect\b',
        r'\bselect\b.*\bfrom\b',
        r'\binsert\b.*\binto\b',
        r'\bupdate\b.*\bset\b',
        r'\bdelete\b.*\bfrom\b',
        r'\bdrop\b.*\btable\b',
        r'\balter\b.*\btable\b',
        r'--',
        r'/\*.*\*/',
        r'\bexec\b',
        r'\bexecute\b',
        r'\bsp_\w+',
        r'\bxp_\w+',
    ]
    
    value_lower = str(value).lower()
    
    for pattern in sql_patterns:
        if re.search(pattern, value_lower, re.IGNORECASE):
            raise ValidationError(
                _('入力値に不正な文字列が含まれています。'),
                code='potential_sql_injection'
            )


def validate_no_xss(value):
    """
    XSS攻撃パターンをチェックする関数
    """
    if not value:
        return
    
    # 危険なXSSパターン
    xss_patterns = [
        r'<script[^>]*>',
        r'</script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
        r'onfocus\s*=',
        r'onblur\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
        r'expression\s*\(',
        r'url\s*\(',
        r'@import',
    ]
    
    value_lower = str(value).lower()
    
    for pattern in xss_patterns:
        if re.search(pattern, value_lower, re.IGNORECASE):
            raise ValidationError(
                _('入力値に不正な文字列が含まれています。'),
                code='potential_xss'
            )


def validate_no_path_traversal(value):
    """
    パストラバーサル攻撃パターンをチェックする関数
    """
    if not value:
        return
    
    # 危険なパストラバーサルパターン
    traversal_patterns = [
        r'\.\./+',
        r'\.\.\\+',
        r'%2e%2e%2f',
        r'%2e%2e%5c',
        r'\.\.%2f',
        r'\.\.%5c',
    ]
    
    value_lower = str(value).lower()
    
    for pattern in traversal_patterns:
        if re.search(pattern, value_lower, re.IGNORECASE):
            raise ValidationError(
                _('入力値に不正な文字列が含まれています。'),
                code='potential_path_traversal'
            )


def comprehensive_input_validation(value, field_name='入力値'):
    """
    包括的な入力値検証を行う関数
    
    - SQLインジェクション対策
    - XSS対策
    - パストラバーサル対策
    """
    if not value:
        return value
    
    try:
        validate_no_sql_injection(value)
        validate_no_xss(value)
        validate_no_path_traversal(value)
        return sanitize_input(value)
    except ValidationError as e:
        # より具体的なエラーメッセージに変更
        raise ValidationError(
            _(f'{field_name}に不正な文字列が含まれています。'),
            code='security_validation_failed'
        )