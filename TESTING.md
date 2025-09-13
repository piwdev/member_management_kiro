# Testing Documentation

## Overview

This document describes the comprehensive testing strategy for the Asset License Management System. The testing suite includes unit tests, integration tests, API tests, security tests, and performance tests.

## Test Structure

```
tests/
├── __init__.py
├── test_integration.py          # System integration tests
├── conftest.py                  # Pytest configuration and fixtures
└── factories.py                 # Test data factories

apps/
├── authentication/
│   └── tests.py                 # Authentication tests
├── employees/
│   └── tests.py                 # Employee management tests
├── devices/
│   └── tests.py                 # Device management tests
├── licenses/
│   └── tests.py                 # License management tests
├── permissions/
│   └── tests.py                 # Permission system tests
├── reports/
│   └── tests.py                 # Reporting system tests
└── dashboard/
    └── tests.py                 # Dashboard tests

fixtures/
└── test_data.json               # Test data fixtures
```

## Test Categories

### Unit Tests
- **Purpose**: Test individual components in isolation
- **Coverage**: Models, serializers, utilities, business logic
- **Marker**: `@pytest.mark.unit`
- **Run with**: `python run_tests.py --unit`

### Integration Tests
- **Purpose**: Test interaction between components
- **Coverage**: Complete workflows, cross-app functionality
- **Marker**: `@pytest.mark.integration`
- **Run with**: `python run_tests.py --integration`

### API Tests
- **Purpose**: Test REST API endpoints
- **Coverage**: Authentication, CRUD operations, permissions
- **Marker**: `@pytest.mark.api`
- **Run with**: `python run_tests.py --api`

### Security Tests
- **Purpose**: Test security features and vulnerabilities
- **Coverage**: Authentication, authorization, input validation
- **Marker**: `@pytest.mark.security`
- **Run with**: `python run_tests.py --security`

### Performance Tests
- **Purpose**: Test system performance under load
- **Coverage**: Response times, database queries, memory usage
- **Marker**: `@pytest.mark.performance`
- **Run with**: `python run_tests.py --performance`

## Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py

# Run specific app tests
python run_tests.py authentication devices

# Run with coverage
python run_tests.py --coverage

# Run specific test categories
python run_tests.py --unit
python run_tests.py --integration
python run_tests.py --api
```

### Test Runner Options

```bash
# Using pytest (default)
python run_tests.py --runner pytest

# Using Django test runner
python run_tests.py --runner django

# Verbose output
python run_tests.py -v 2

# Stop on first failure
python run_tests.py --failfast

# Run in parallel
python run_tests.py --parallel 4

# Keep test database
python run_tests.py --keepdb
```

### Test Data Management

```bash
# Set up basic test data
python run_tests.py --setup-data

# Set up comprehensive test data
python run_tests.py --setup-data --comprehensive

# Clean up test data
python run_tests.py --cleanup
```

## Test Configuration

### Settings
- Test settings: `asset_management.settings.test`
- In-memory SQLite database for speed
- Disabled migrations for faster test runs
- Simplified password hashing
- Null logging handler

### Fixtures
- Basic test data in `fixtures/test_data.json`
- Factory classes for generating test objects
- Management command for comprehensive test data

### Coverage Requirements
- Minimum coverage: 80%
- Coverage reports: HTML and terminal
- Excludes: migrations, settings, test files

## Test Data

### Basic Test Data (Fixtures)
- Admin user and regular users
- Sample employees from different departments
- Various device types and models
- Software licenses with different pricing models
- Permission policies for departments and positions

### Comprehensive Test Data (Management Command)
- 100+ employees across multiple departments
- 50+ devices of various types
- 20+ software licenses
- Complex permission policies and overrides
- Historical data and assignments

## Writing Tests

### Test Naming Convention
```python
class TestModelName:
    def test_method_name_should_expected_behavior(self):
        """Test description."""
        pass
```

### Test Structure
```python
def test_feature_name(self):
    """Test description."""
    # Arrange
    setup_test_data()
    
    # Act
    result = perform_action()
    
    # Assert
    assert result == expected_value
```

### Using Fixtures
```python
@pytest.fixture
def sample_employee():
    return Employee.objects.create(
        employee_id='TEST001',
        name='Test Employee',
        # ... other fields
    )

def test_employee_creation(sample_employee):
    assert sample_employee.employee_id == 'TEST001'
```

### Mocking External Dependencies
```python
@patch('apps.authentication.backends.LDAPBackend.authenticate')
def test_ldap_fallback(mock_ldap):
    mock_ldap.return_value = None
    # Test local authentication fallback
```

## Test Examples

### Model Test
```python
def test_device_assignment(self):
    """Test device assignment to employee."""
    device = Device.objects.create(
        type='LAPTOP',
        manufacturer='Dell',
        model='Test Model',
        serial_number='TEST001',
        purchase_date=date.today(),
        warranty_expiry=date.today() + timedelta(days=365)
    )
    
    employee = Employee.objects.create(
        employee_id='EMP001',
        name='Test Employee',
        # ... other required fields
    )
    
    assignment = device.assign_to_employee(
        employee=employee,
        purpose='Testing',
        assigned_by=self.admin_user
    )
    
    assert assignment.status == 'ACTIVE'
    assert device.status == 'ASSIGNED'
    assert device.current_assignment == assignment
```

### API Test
```python
def test_device_list_api(self):
    """Test device list API endpoint."""
    self.client.force_authenticate(user=self.admin_user)
    
    response = self.client.get('/api/devices/devices/')
    
    assert response.status_code == 200
    assert 'results' in response.data
    assert len(response.data['results']) > 0
```

### Integration Test
```python
def test_complete_employee_lifecycle(self):
    """Test complete employee lifecycle from hiring to termination."""
    # Create employee
    employee = Employee.objects.create(...)
    
    # Assign resources
    device_assignment = device.assign_to_employee(employee, ...)
    license_assignment = LicenseAssignment.objects.create(...)
    
    # Terminate employee
    employee.terminate_employment(...)
    
    # Verify resource recovery
    assert device.status == 'AVAILABLE'
    assert license.available_count == original_count
```

## Continuous Integration

### GitHub Actions (Example)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python run_tests.py --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: tests
        name: tests
        entry: python run_tests.py --failfast
        language: system
        pass_filenames: false
        always_run: true
```

## Performance Testing

### Database Query Optimization
```python
def test_query_count(self):
    """Test that list view doesn't cause N+1 queries."""
    with self.assertNumQueries(3):  # Expected number of queries
        response = self.client.get('/api/devices/devices/')
        assert response.status_code == 200
```

### Response Time Testing
```python
def test_api_response_time(self):
    """Test API response time is acceptable."""
    import time
    
    start_time = time.time()
    response = self.client.get('/api/devices/devices/')
    end_time = time.time()
    
    response_time = end_time - start_time
    assert response_time < 1.0  # Should respond within 1 second
```

## Security Testing

### Authentication Testing
```python
def test_unauthenticated_access(self):
    """Test that unauthenticated users cannot access protected endpoints."""
    response = self.client.get('/api/devices/devices/')
    assert response.status_code == 401
```

### Authorization Testing
```python
def test_regular_user_cannot_create_device(self):
    """Test that regular users cannot create devices."""
    self.client.force_authenticate(user=self.regular_user)
    response = self.client.post('/api/devices/devices/', {})
    assert response.status_code == 403
```

### Input Validation Testing
```python
def test_sql_injection_protection(self):
    """Test protection against SQL injection."""
    malicious_input = "'; DROP TABLE devices; --"
    response = self.client.get(f'/api/devices/devices/?search={malicious_input}')
    assert response.status_code != 500  # Should not cause server error
```

## Troubleshooting

### Common Issues

1. **Test Database Issues**
   ```bash
   # Reset test database
   python run_tests.py --cleanup
   python run_tests.py --setup-data
   ```

2. **Migration Issues**
   ```bash
   # Run with migrations
   python manage.py test --settings=asset_management.settings.test
   ```

3. **Coverage Issues**
   ```bash
   # Generate detailed coverage report
   python run_tests.py --coverage
   open htmlcov/index.html
   ```

4. **Slow Tests**
   ```bash
   # Run in parallel
   python run_tests.py --parallel 4
   
   # Use pytest-xdist
   python -m pytest -n auto
   ```

### Debugging Tests
```python
import pytest

def test_debug_example():
    """Example of debugging a test."""
    # Use pytest.set_trace() for debugging
    pytest.set_trace()
    
    # Or use print statements
    print(f"Debug info: {variable}")
    
    # Or use logging
    import logging
    logging.debug("Debug message")
```

## Best Practices

1. **Test Independence**: Each test should be independent and not rely on other tests
2. **Clear Naming**: Use descriptive test names that explain what is being tested
3. **Arrange-Act-Assert**: Structure tests with clear setup, action, and verification phases
4. **Mock External Dependencies**: Mock external services, APIs, and file system operations
5. **Test Edge Cases**: Include tests for boundary conditions and error scenarios
6. **Keep Tests Fast**: Use in-memory databases and minimal test data
7. **Regular Maintenance**: Update tests when code changes and remove obsolete tests

## Metrics and Reporting

### Coverage Metrics
- Line coverage: >80%
- Branch coverage: >70%
- Function coverage: >90%

### Test Metrics
- Total tests: 500+
- Test execution time: <5 minutes
- Test success rate: >99%

### Quality Gates
- All tests must pass before merge
- Coverage must not decrease
- No security vulnerabilities
- Performance regression checks