# License Management API Documentation

## Overview

The License Management API provides comprehensive functionality for managing software licenses, assignments, and monitoring. It includes features for license CRUD operations, assignment management, usage statistics, cost analysis, and expiry monitoring.

## Authentication

All endpoints require authentication. Use JWT tokens in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Permissions

- **Admin users** (is_staff=True): Full access to all operations
- **Regular users**: Read-only access to license information, can view their own assignments

## Endpoints

### License Management

#### GET /api/licenses/licenses/
List all licenses with filtering options.

**Query Parameters:**
- `software_name`: Filter by software name (case-insensitive contains)
- `license_type`: Filter by license type
- `pricing_model`: Filter by pricing model (MONTHLY, YEARLY, PERPETUAL)
- `expiring_soon`: Show licenses expiring within 30 days (true/false)
- `expired`: Show expired licenses (true/false)
- `fully_utilized`: Show fully utilized licenses (true/false)
- `department`: Filter by assigned employee department

**Response:**
```json
[
  {
    "id": "uuid",
    "software_name": "Microsoft Office",
    "license_type": "Standard",
    "total_count": 10,
    "available_count": 8,
    "used_count": 2,
    "usage_percentage": 20.0,
    "expiry_date": "2025-12-31",
    "pricing_model": "YEARLY",
    "unit_price": "100.00",
    "monthly_cost": 16.67,
    "yearly_cost": 200.00,
    "is_expiring_soon": false,
    "days_until_expiry": 483
  }
]
```

#### POST /api/licenses/licenses/
Create a new license (Admin only).

**Request Body:**
```json
{
  "software_name": "Adobe Photoshop",
  "license_type": "Professional",
  "total_count": 5,
  "available_count": 5,
  "expiry_date": "2025-12-31",
  "pricing_model": "MONTHLY",
  "unit_price": "50.00",
  "vendor_name": "Adobe Inc.",
  "description": "Professional photo editing software"
}
```

#### GET /api/licenses/licenses/{id}/
Get detailed information about a specific license.

#### PUT /api/licenses/licenses/{id}/
Update a license (Admin only).

#### DELETE /api/licenses/licenses/{id}/
Delete a license (Admin only).

### License Assignment

#### POST /api/licenses/licenses/{id}/assign/
Assign a license to an employee (Admin only).

**Request Body:**
```json
{
  "employee_id": "uuid",
  "start_date": "2025-09-04",
  "end_date": "2026-09-04",
  "purpose": "Development work",
  "notes": "Required for project X"
}
```

**Response:**
```json
{
  "id": "uuid",
  "license_info": {
    "id": "uuid",
    "software_name": "Microsoft Office",
    "license_type": "Standard",
    "expiry_date": "2025-12-31"
  },
  "employee_info": {
    "id": "uuid",
    "employee_id": "EMP001",
    "name": "John Doe",
    "department": "IT",
    "position": "Developer"
  },
  "assigned_date": "2025-09-04",
  "start_date": "2025-09-04",
  "end_date": "2026-09-04",
  "purpose": "Development work",
  "status": "ACTIVE"
}
```

#### POST /api/licenses/licenses/{id}/revoke/
Revoke a license assignment (Admin only).

**Request Body:**
```json
{
  "employee_id": "uuid",
  "notes": "No longer needed"
}
```

#### GET /api/licenses/licenses/{id}/assignments/
Get all assignments for a specific license.

**Query Parameters:**
- `status`: Filter by assignment status (ACTIVE, EXPIRED, REVOKED)

### License Assignment Management

#### GET /api/licenses/assignments/
List all license assignments with filtering.

**Query Parameters:**
- `license`: Filter by license ID
- `employee`: Filter by employee ID
- `status`: Filter by assignment status
- `department`: Filter by employee department
- `expiring_soon`: Show assignments expiring within 30 days (true/false)

#### POST /api/licenses/assignments/
Create a new license assignment (Admin only).

**Request Body:**
```json
{
  "license": "uuid",
  "employee": "uuid",
  "start_date": "2025-09-04",
  "end_date": "2026-09-04",
  "purpose": "Development work"
}
```

#### GET /api/licenses/assignments/{id}/
Get detailed information about a specific assignment.

#### PUT /api/licenses/assignments/{id}/
Update an assignment (Admin only).

#### POST /api/licenses/assignments/{id}/revoke/
Revoke a specific assignment (Admin only).

#### GET /api/licenses/assignments/my_assignments/
Get assignments for the current user (requires employee profile).

### Statistics and Analytics

#### GET /api/licenses/licenses/usage_stats/
Get comprehensive license usage statistics and alerts.

**Response:**
```json
{
  "total_licenses": 25,
  "active_licenses": 23,
  "expired_licenses": 2,
  "expiring_soon_licenses": 3,
  "fully_utilized_licenses": 5,
  "total_monthly_cost": "2500.00",
  "total_yearly_cost": "30000.00",
  "expiring_licenses": [
    {
      "id": "uuid",
      "software_name": "Expiring Software",
      "expiry_date": "2025-09-15",
      "usage_percentage": 80.0
    }
  ],
  "over_utilized_licenses": [
    {
      "id": "uuid",
      "software_name": "Fully Used Software",
      "available_count": 0,
      "total_count": 10
    }
  ]
}
```

#### GET /api/licenses/licenses/cost_analysis/
Get detailed cost analysis by software, department, or license type.

**Query Parameters:**
- `group_by`: Grouping method (software, department, license_type)
- `department`: Filter by specific department

**Response:**
```json
[
  {
    "software_name": "Microsoft Office",
    "license_type": "Standard",
    "total_licenses": 10,
    "used_licenses": 8,
    "monthly_cost": "133.33",
    "yearly_cost": "1600.00",
    "usage_percentage": 80.0
  }
]
```

#### GET /api/licenses/licenses/expiring_alerts/
Get licenses expiring within specified days.

**Query Parameters:**
- `days`: Number of days to look ahead (default: 30)

**Response:**
```json
{
  "days_ahead": 30,
  "count": 3,
  "licenses": [
    {
      "id": "uuid",
      "software_name": "Expiring Software",
      "expiry_date": "2025-09-15",
      "days_until_expiry": 11
    }
  ]
}
```

## Error Responses

All endpoints return appropriate HTTP status codes and error messages:

### 400 Bad Request
```json
{
  "error": "利用可能なライセンス数が不足しています。利用可能: 0"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "error": "指定された社員が見つかりません。"
}
```

### 409 Conflict
```json
{
  "error": "この社員には既に同じライセンスが割り当てられています。"
}
```

## Management Commands

### check_license_expiry
Monitor license expiry and update assignment statuses.

```bash
# Check for licenses expiring within 30 days
python manage.py check_license_expiry

# Check for licenses expiring within 7 days
python manage.py check_license_expiry --days 7

# Dry run (no database changes)
python manage.py check_license_expiry --dry-run
```

This command should be run daily via cron job for automatic license monitoring.

## Business Logic

### License Assignment Rules
1. Only active employees can be assigned licenses
2. Only one active assignment per license-employee pair
3. Cannot assign expired licenses
4. Cannot assign more licenses than available count
5. License count is automatically updated when assignments are created/revoked

### Cost Calculations
- **Monthly Cost**: Based on used licenses and pricing model
- **Yearly Cost**: Calculated from monthly cost or direct yearly pricing
- **Total Cost**: For perpetual licenses, total purchase cost; for subscriptions, yearly cost

### Expiry Monitoring
- Licenses expiring within 30 days trigger alerts
- Expired assignments are automatically marked as EXPIRED
- License counts are released when assignments expire or are revoked

### Audit Trail
- All license and assignment changes are tracked with timestamps and user information
- Assignment history includes creation, modification, and revocation details