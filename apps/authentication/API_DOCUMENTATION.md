# Authentication API Documentation

## Overview

The authentication system provides secure JWT-based authentication with LDAP integration, account lockout protection, and comprehensive security logging.

## Base URL

All authentication endpoints are prefixed with `/api/auth/`

## Authentication

Most endpoints require JWT authentication. Include the access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## Endpoints

### 1. Login

**POST** `/api/auth/login/`

Authenticate user and receive JWT tokens.

#### Request Body

```json
{
  "username": "string",
  "password": "string"
}
```

#### Response (200 OK)

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "full_name": "string",
    "employee_id": "string",
    "department": "string",
    "position": "string",
    "location": "TOKYO|OKINAWA|REMOTE",
    "is_active": true,
    "is_staff": false,
    "is_superuser": false,
    "is_account_locked": false,
    "last_login": "2024-01-01T00:00:00Z",
    "date_joined": "2024-01-01T00:00:00Z",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

#### Error Responses

- **401 Unauthorized**: Invalid credentials
- **401 Unauthorized**: Account locked
- **401 Unauthorized**: Account inactive

#### Security Features

- Account lockout after 5 failed attempts (30 minutes)
- Login attempt logging with IP address and user agent
- Rate limiting (10 attempts per minute per IP)

### 2. Token Refresh

**POST** `/api/auth/refresh/`

Refresh access token using refresh token.

#### Request Body

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Response (200 OK)

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 3. Logout

**POST** `/api/auth/logout/`

Logout user and blacklist refresh token.

**Authentication Required**

#### Request Body

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Response (200 OK)

```json
{
  "message": "ログアウトしました。"
}
```

### 4. Current User Info

**GET** `/api/auth/me/`

Get current authenticated user information.

**Authentication Required**

#### Response (200 OK)

```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "full_name": "string",
  "employee_id": "string",
  "department": "string",
  "position": "string",
  "location": "TOKYO|OKINAWA|REMOTE",
  "is_active": true,
  "is_staff": false,
  "is_superuser": false,
  "is_account_locked": false,
  "last_login": "2024-01-01T00:00:00Z",
  "date_joined": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### 5. Change Password

**POST** `/api/auth/change-password/`

Change current user's password.

**Authentication Required**

#### Request Body

```json
{
  "old_password": "string",
  "new_password": "string",
  "confirm_password": "string"
}
```

#### Response (200 OK)

```json
{
  "message": "パスワードが正常に変更されました。"
}
```

#### Error Responses

- **400 Bad Request**: Invalid old password
- **400 Bad Request**: Password confirmation mismatch
- **400 Bad Request**: New password too weak

## Admin Endpoints

The following endpoints require admin privileges (`is_staff=True`).

### 6. User Management

**GET** `/api/auth/users/`

List all users with filtering and search capabilities.

**Admin Authentication Required**

#### Query Parameters

- `search`: Search in username, first_name, last_name, email, employee_id
- `department`: Filter by department
- `is_active`: Filter by active status (true/false)
- `page`: Page number for pagination
- `page_size`: Number of results per page

#### Response (200 OK)

```json
{
  "count": 100,
  "next": "http://example.com/api/auth/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "username": "string",
      "email": "string",
      "first_name": "string",
      "last_name": "string",
      "full_name": "string",
      "employee_id": "string",
      "department": "string",
      "position": "string",
      "location": "TOKYO|OKINAWA|REMOTE",
      "is_active": true,
      "is_staff": false,
      "is_superuser": false,
      "is_account_locked": false,
      "last_login": "2024-01-01T00:00:00Z",
      "date_joined": "2024-01-01T00:00:00Z",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 7. Unlock User Account

**POST** `/api/auth/users/{user_id}/unlock_account/`

Unlock a locked user account.

**Admin Authentication Required**

#### Response (200 OK)

```json
{
  "message": "ユーザー {username} のアカウントロックを解除しました。"
}
```

### 8. Reset User Password

**POST** `/api/auth/users/{user_id}/reset_password/`

Reset a user's password (admin only).

**Admin Authentication Required**

#### Request Body

```json
{
  "new_password": "string"
}
```

#### Response (200 OK)

```json
{
  "message": "ユーザー {username} のパスワードをリセットしました。"
}
```

### 9. Login Attempts

**GET** `/api/auth/login-attempts/`

View login attempt logs for security monitoring.

**Admin Authentication Required**

#### Query Parameters

- `username`: Filter by username
- `success`: Filter by success status (true/false)
- `ip_address`: Filter by IP address
- `date_from`: Filter from date (YYYY-MM-DD)
- `date_to`: Filter to date (YYYY-MM-DD)
- `page`: Page number for pagination

#### Response (200 OK)

```json
{
  "count": 50,
  "next": "http://example.com/api/auth/login-attempts/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": "uuid",
      "user_display": "John Doe",
      "username": "john.doe",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "success": true,
      "failure_reason": "",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ]
}
```

## Security Features

### Account Lockout

- Accounts are automatically locked after 5 consecutive failed login attempts
- Lockout duration: 30 minutes
- Admins can manually unlock accounts
- Failed attempt counter resets on successful login

### Rate Limiting

- Login endpoint: 10 attempts per minute per IP address
- Returns HTTP 429 when limit exceeded

### Security Logging

All authentication events are logged including:
- Successful and failed login attempts
- Account lockouts and unlocks
- Password changes
- Suspicious activities

### JWT Token Security

- Access tokens expire after 1 hour
- Refresh tokens expire after 7 days
- Refresh token rotation enabled
- Token blacklisting on logout

### LDAP Integration

When LDAP is configured:
- Users authenticate against LDAP server
- User attributes are synchronized from LDAP
- Local account lockout still applies
- Fallback to local authentication if LDAP unavailable

## Error Handling

### Standard Error Response Format

```json
{
  "error": "Error message in Japanese"
}
```

### Field Validation Errors

```json
{
  "field_name": ["Error message for this field"]
}
```

### HTTP Status Codes

- `200 OK`: Success
- `400 Bad Request`: Validation error
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Usage Examples

### Login Flow

```javascript
// 1. Login
const loginResponse = await fetch('/api/auth/login/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'john.doe',
    password: 'password123'
  })
});

const { access, refresh, user } = await loginResponse.json();

// 2. Store tokens
localStorage.setItem('access_token', access);
localStorage.setItem('refresh_token', refresh);

// 3. Use access token for authenticated requests
const userResponse = await fetch('/api/auth/me/', {
  headers: {
    'Authorization': `Bearer ${access}`
  }
});

// 4. Refresh token when needed
const refreshResponse = await fetch('/api/auth/refresh/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    refresh: refresh
  })
});

// 5. Logout
await fetch('/api/auth/logout/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    refresh: refresh
  })
});
```

### Admin Operations

```javascript
// Get user list with search
const usersResponse = await fetch('/api/auth/users/?search=john&department=IT', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});

// Unlock user account
await fetch(`/api/auth/users/${userId}/unlock_account/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});

// View login attempts
const attemptsResponse = await fetch('/api/auth/login-attempts/?success=false', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```