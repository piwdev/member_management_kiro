# Reports API Documentation

## Overview

The Reports API provides comprehensive analytics and reporting functionality for the asset management system. It includes usage statistics, inventory status, cost analysis, and export capabilities.

## Authentication

All endpoints require authentication. Admin users have full access, while regular users have read-only access.

## Endpoints

### 1. Usage Statistics

**GET** `/api/reports/usage-statistics/`

Get comprehensive usage statistics with department, position, and period analysis.

**Query Parameters:**
- `department` (optional): Filter by department name
- `position` (optional): Filter by position/role
- `start_date` (optional): Start date for analysis (YYYY-MM-DD format)
- `end_date` (optional): End date for analysis (YYYY-MM-DD format)

**Response:**
```json
{
  "success": true,
  "data": {
    "department_stats": {
      "IT": {
        "employee_count": 15,
        "device_assignments": 18,
        "license_assignments": 45,
        "unique_devices": 12,
        "unique_licenses": 8,
        "avg_devices_per_employee": 1.2,
        "avg_licenses_per_employee": 3.0
      }
    },
    "position_stats": {
      "Developer": {
        "employee_count": 10,
        "device_assignments": 12,
        "license_assignments": 30
      }
    },
    "device_usage": {
      "device_type_usage": [
        {"device__type": "LAPTOP", "count": 15, "unique_devices": 12}
      ],
      "popular_devices": [
        {"device__manufacturer": "Dell", "device__model": "Latitude", "assignment_count": 8}
      ],
      "total_assignments": 25,
      "active_assignments": 20,
      "avg_assignment_duration_days": 45.5
    },
    "license_usage": {
      "software_usage": [
        {"license__software_name": "Microsoft Office", "assignment_count": 15}
      ],
      "total_assignments": 50,
      "active_assignments": 45
    },
    "period_summary": {
      "period_start": "2024-01-01",
      "period_end": "2024-12-31",
      "new_device_assignments": 5,
      "new_license_assignments": 12,
      "device_returns": 2,
      "license_revocations": 3
    },
    "generated_at": "2024-01-15T10:30:00Z",
    "filters": {"department": "IT"}
  }
}
```

### 2. Inventory Status

**GET** `/api/reports/inventory-status/`

Get inventory status with utilization rates and shortage predictions.

**Query Parameters:**
- `device_type` (optional): Filter by device type (LAPTOP, DESKTOP, TABLET, SMARTPHONE)
- `software_name` (optional): Filter by software name (partial match)

**Response:**
```json
{
  "success": true,
  "data": {
    "device_inventory": {
      "total_devices": 50,
      "status_breakdown": [
        {"status": "AVAILABLE", "count": 20},
        {"status": "ASSIGNED", "count": 25},
        {"status": "MAINTENANCE", "count": 5}
      ],
      "type_breakdown": [
        {
          "type": "LAPTOP",
          "total": 30,
          "available": 12,
          "assigned": 15,
          "maintenance": 3
        }
      ]
    },
    "license_inventory": {
      "license_details": [
        {
          "software_name": "Microsoft Office",
          "license_type": "Standard",
          "total_count": 50,
          "used_count": 35,
          "available_count": 15,
          "utilization_percentage": 70.0,
          "is_fully_utilized": false,
          "expires_soon": false,
          "is_expired": false
        }
      ],
      "summary": {
        "total_licenses": 200,
        "total_used": 150,
        "total_available": 50,
        "overall_utilization": 75.0
      }
    },
    "utilization_rates": {
      "device_utilization": {
        "LAPTOP": {
          "total": 30,
          "assigned": 15,
          "utilization_percentage": 50.0
        }
      },
      "license_utilization": {
        "Microsoft Office (Standard)": {
          "total": 50,
          "used": 35,
          "utilization_percentage": 70.0
        }
      }
    },
    "shortage_predictions": [
      {
        "resource_type": "license",
        "resource_name": "Adobe Creative Suite (Professional)",
        "current_available": 2,
        "total": 20,
        "severity": "MEDIUM",
        "recommendation": "Adobe Creative Suiteのライセンス追加購入を検討してください"
      }
    ]
  }
}
```

### 3. Cost Analysis

**GET** `/api/reports/cost-analysis/`

Get comprehensive cost analysis with department costs and software cost trends.

**Query Parameters:**
- `department` (optional): Filter by department name
- `start_date` (optional): Start date for analysis (YYYY-MM-DD format)
- `end_date` (optional): End date for analysis (YYYY-MM-DD format)

**Response:**
```json
{
  "success": true,
  "data": {
    "department_costs": {
      "IT": {
        "employee_count": 15,
        "license_assignments": 45,
        "monthly_cost": 15000.0,
        "yearly_cost": 180000.0,
        "avg_cost_per_employee": 1000.0,
        "license_breakdown": {
          "Microsoft Office (Standard)": {
            "assignments": 15,
            "monthly_cost": 7500.0,
            "yearly_cost": 90000.0,
            "pricing_model": "YEARLY"
          }
        }
      }
    },
    "software_costs": {
      "Microsoft Office (Standard)": {
        "license_id": "uuid-here",
        "total_licenses": 50,
        "used_licenses": 35,
        "utilization_percentage": 70.0,
        "pricing_model": "YEARLY",
        "unit_price": 6000.0,
        "monthly_cost": 17500.0,
        "yearly_cost": 210000.0,
        "cost_per_user": 500.0,
        "expiry_date": "2024-12-31",
        "is_expiring_soon": false,
        "departments_using": ["IT", "Marketing", "Sales"]
      }
    },
    "cost_trends": {
      "2024-01": {
        "month": "2024-01",
        "total_cost": 25000.0,
        "assignment_count": 50,
        "avg_cost_per_assignment": 500.0
      }
    },
    "budget_comparison": {
      "IT": {
        "actual_cost": 180000.0,
        "estimated_budget": 198000.0,
        "variance": -18000.0,
        "variance_percentage": -9.1,
        "status": "UNDER_BUDGET"
      }
    }
  }
}
```

### 4. Department Usage

**GET** `/api/reports/department-usage/`

Get detailed usage statistics by department.

**Query Parameters:**
- `start_date` (optional): Start date for analysis (YYYY-MM-DD format)
- `end_date` (optional): End date for analysis (YYYY-MM-DD format)

### 5. Position Usage

**GET** `/api/reports/position-usage/`

Get detailed usage statistics by position/role.

**Query Parameters:**
- `start_date` (optional): Start date for analysis (YYYY-MM-DD format)
- `end_date` (optional): End date for analysis (YYYY-MM-DD format)

### 6. Export Report

**POST** `/api/reports/export/`

Export report data in CSV or PDF format.

**Request Body:**
```json
{
  "format": "csv",
  "report_type": "usage_stats",
  "filters": {
    "department": "IT",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }
}
```

**Parameters:**
- `format`: Export format ("csv" or "pdf")
- `report_type`: Type of report ("usage_stats", "inventory_status", "cost_analysis")
- `filters`: Optional filters to apply to the report

**Response:**
Returns the exported file with appropriate content-type headers.

## Error Responses

All endpoints return error responses in the following format:

```json
{
  "error": "Error message",
  "details": "Additional error details or validation errors"
}
```

**Common HTTP Status Codes:**
- `200 OK`: Successful request
- `400 Bad Request`: Invalid parameters or request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `500 Internal Server Error`: Server error

## Caching

Reports are automatically cached for performance optimization:
- Usage statistics: Cached for 1 hour
- Inventory status: Cached for 2 hours
- Cost analysis: Cached for 2 hours

Cache keys are generated based on report type and filter parameters.

## Management Commands

### Generate Cost Report

```bash
python manage.py generate_cost_report --department IT --start-date 2024-01-01 --end-date 2024-12-31 --output report.json
```

**Options:**
- `--department`: Filter by department
- `--start-date`: Start date (YYYY-MM-DD)
- `--end-date`: End date (YYYY-MM-DD)
- `--output`: Output file path (optional, prints to console if not specified)