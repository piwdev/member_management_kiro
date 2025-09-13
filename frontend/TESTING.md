# Frontend Testing Documentation

## Overview

This document describes the comprehensive testing strategy for the React frontend of the Asset License Management System. The testing suite includes unit tests, integration tests, and end-to-end (E2E) tests.

## Test Structure

```
frontend/
├── src/
│   ├── __tests__/
│   │   └── integration.test.tsx    # Integration tests
│   ├── components/
│   │   ├── auth/
│   │   │   └── __tests__/
│   │   │       └── LoginForm.test.tsx
│   │   ├── employees/
│   │   │   └── __tests__/
│   │   │       └── EmployeeList.test.tsx
│   │   ├── devices/
│   │   │   └── __tests__/
│   │   │       └── DeviceManagement.test.tsx
│   │   ├── dashboard/
│   │   │   └── __tests__/
│   │   │       └── EmployeeDashboard.test.tsx
│   │   └── reports/
│   │       └── __tests__/
│   │           └── ReportsManagement.test.tsx
│   ├── test-utils.tsx              # Testing utilities
│   └── setupTests.ts               # Test setup
├── e2e/
│   ├── auth.spec.ts                # E2E authentication tests
│   └── employee-management.spec.ts # E2E employee management tests
├── jest.config.js                  # Jest configuration
└── playwright.config.ts            # Playwright configuration
```

## Test Categories

### Unit Tests
- **Purpose**: Test individual components in isolation
- **Tools**: Jest, React Testing Library
- **Coverage**: Components, hooks, utilities
- **Location**: `src/components/**/__tests__/`

### Integration Tests
- **Purpose**: Test component interactions and workflows
- **Tools**: Jest, React Testing Library, MSW
- **Coverage**: Complete user workflows, API integration
- **Location**: `src/__tests__/integration.test.tsx`

### End-to-End Tests
- **Purpose**: Test complete user journeys in real browser
- **Tools**: Playwright
- **Coverage**: Authentication, navigation, critical workflows
- **Location**: `e2e/`

## Running Tests

### Unit and Integration Tests

```bash
# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in CI mode
npm run test:ci

# Run specific test file
npm test LoginForm.test.tsx

# Run tests in watch mode
npm test -- --watch
```

### End-to-End Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui

# Run E2E tests in headed mode (visible browser)
npm run test:e2e:headed

# Debug E2E tests
npm run test:e2e:debug

# Run specific E2E test
npx playwright test auth.spec.ts
```

## Test Configuration

### Jest Configuration
- **Environment**: jsdom
- **Setup**: `src/setupTests.ts`
- **Coverage threshold**: 80% lines, 70% branches
- **Mocks**: localStorage, fetch, IntersectionObserver

### Playwright Configuration
- **Browsers**: Chromium, Firefox, WebKit
- **Mobile**: Chrome Mobile, Safari Mobile
- **Base URL**: http://localhost:3000
- **Reporters**: HTML, JSON, JUnit

## Testing Utilities

### Custom Render Function
```typescript
import { render } from '../test-utils';

// Renders component with all providers
render(<MyComponent />, {
  authValue: mockAuthContextValue,
  queryClient: customQueryClient,
  initialEntries: ['/custom-route']
});
```

### Mock Data
```typescript
import { mockApiResponses, mockUser, mockAdminUser } from '../test-utils';

// Use predefined mock data
mockFetch.mockResolvedValue({
  ok: true,
  json: () => Promise.resolve(mockApiResponses.employees)
});
```

### API Mocking
```typescript
// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock specific API response
mockFetch.mockResolvedValueOnce({
  ok: true,
  json: () => Promise.resolve({ data: 'mock data' })
});
```

## Writing Tests

### Component Test Example
```typescript
import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from '../../../test-utils';
import MyComponent from '../MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });

  it('handles user interaction', async () => {
    const user = userEvent.setup();
    render(<MyComponent />);

    await user.click(screen.getByRole('button', { name: 'Click Me' }));

    await waitFor(() => {
      expect(screen.getByText('Clicked!')).toBeInTheDocument();
    });
  });
});
```

### API Integration Test Example
```typescript
it('fetches and displays data', async () => {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: () => Promise.resolve({ results: [{ id: 1, name: 'Test' }] })
  });

  render(<DataComponent />);

  await waitFor(() => {
    expect(screen.getByText('Test')).toBeInTheDocument();
  });

  expect(mockFetch).toHaveBeenCalledWith(
    expect.stringContaining('/api/data/'),
    expect.any(Object)
  );
});
```

### E2E Test Example
```typescript
import { test, expect } from '@playwright/test';

test('user can login', async ({ page }) => {
  await page.goto('/login');

  await page.getByLabel('Username').fill('testuser');
  await page.getByLabel('Password').fill('password123');
  await page.getByRole('button', { name: 'Login' }).click();

  await expect(page).toHaveURL('/dashboard');
  await expect(page.getByText('Dashboard')).toBeVisible();
});
```

## Test Patterns

### Arrange-Act-Assert Pattern
```typescript
it('should update user profile', async () => {
  // Arrange
  const user = userEvent.setup();
  const mockUpdateUser = jest.fn();
  render(<UserProfile onUpdate={mockUpdateUser} />);

  // Act
  await user.type(screen.getByLabelText('Name'), 'New Name');
  await user.click(screen.getByRole('button', { name: 'Save' }));

  // Assert
  expect(mockUpdateUser).toHaveBeenCalledWith({ name: 'New Name' });
});
```

### Testing Async Operations
```typescript
it('shows loading state during API call', async () => {
  mockFetch.mockImplementation(() => new Promise(resolve => 
    setTimeout(resolve, 1000)
  ));

  render(<AsyncComponent />);

  expect(screen.getByText('Loading...')).toBeInTheDocument();

  await waitFor(() => {
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
  });
});
```

### Testing Error States
```typescript
it('displays error message on API failure', async () => {
  mockFetch.mockRejectedValueOnce(new Error('API Error'));

  render(<DataComponent />);

  await waitFor(() => {
    expect(screen.getByText('Error loading data')).toBeInTheDocument();
  });
});
```

### Testing Forms
```typescript
it('validates form input', async () => {
  const user = userEvent.setup();
  render(<LoginForm />);

  await user.click(screen.getByRole('button', { name: 'Submit' }));

  await waitFor(() => {
    expect(screen.getByText('Username is required')).toBeInTheDocument();
    expect(screen.getByText('Password is required')).toBeInTheDocument();
  });
});
```

## Accessibility Testing

### Screen Reader Testing
```typescript
it('is accessible to screen readers', () => {
  render(<MyComponent />);

  expect(screen.getByRole('button', { name: 'Submit' })).toBeInTheDocument();
  expect(screen.getByLabelText('Username')).toBeInTheDocument();
});
```

### Keyboard Navigation Testing
```typescript
it('supports keyboard navigation', async () => {
  const user = userEvent.setup();
  render(<NavigationComponent />);

  await user.tab();
  expect(screen.getByRole('link', { name: 'Home' })).toHaveFocus();

  await user.tab();
  expect(screen.getByRole('link', { name: 'About' })).toHaveFocus();
});
```

## Performance Testing

### Render Performance
```typescript
it('renders efficiently', () => {
  const startTime = performance.now();
  render(<LargeComponent data={largeDataSet} />);
  const endTime = performance.now();

  expect(endTime - startTime).toBeLessThan(100); // 100ms threshold
});
```

### Memory Leak Testing
```typescript
it('cleans up properly on unmount', () => {
  const { unmount } = render(<ComponentWithSubscriptions />);
  
  unmount();
  
  // Verify cleanup (e.g., event listeners removed, subscriptions cancelled)
});
```

## Mocking Strategies

### API Mocking with MSW
```typescript
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  rest.get('/api/users', (req, res, ctx) => {
    return res(ctx.json({ users: [] }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Context Mocking
```typescript
const mockAuthContext = {
  user: mockUser,
  login: jest.fn(),
  logout: jest.fn(),
  isAuthenticated: true
};

render(
  <AuthContext.Provider value={mockAuthContext}>
    <ComponentUnderTest />
  </AuthContext.Provider>
);
```

### Router Mocking
```typescript
import { MemoryRouter } from 'react-router-dom';

render(
  <MemoryRouter initialEntries={['/test-route']}>
    <ComponentWithRouting />
  </MemoryRouter>
);
```

## Coverage Requirements

### Coverage Thresholds
- **Lines**: 80%
- **Functions**: 80%
- **Branches**: 70%
- **Statements**: 80%

### Coverage Reports
- **HTML**: `coverage/lcov-report/index.html`
- **JSON**: `coverage/coverage-final.json`
- **LCOV**: `coverage/lcov.info`

### Excluded Files
- Test files (`*.test.tsx`, `*.spec.tsx`)
- Story files (`*.stories.tsx`)
- Configuration files
- Type definitions (`*.d.ts`)

## Continuous Integration

### GitHub Actions Example
```yaml
name: Frontend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run test:ci
      - run: npm run test:e2e
      - uses: actions/upload-artifact@v3
        with:
          name: coverage
          path: coverage/
```

### Pre-commit Hooks
```json
{
  "husky": {
    "hooks": {
      "pre-commit": "npm run test:ci && npm run lint"
    }
  }
}
```

## Debugging Tests

### Debug Unit Tests
```bash
# Run tests in debug mode
npm test -- --no-cache --detectOpenHandles

# Debug specific test
npm test -- --testNamePattern="specific test name"
```

### Debug E2E Tests
```bash
# Run with browser visible
npm run test:e2e:headed

# Debug mode with breakpoints
npm run test:e2e:debug

# Generate trace
npx playwright test --trace on
```

### Common Issues

1. **Async Operations**: Use `waitFor` for async updates
2. **Cleanup**: Ensure proper cleanup in `afterEach`
3. **Mocking**: Reset mocks between tests
4. **Timing**: Use `findBy*` queries for elements that appear later

## Best Practices

### Test Organization
- Group related tests in `describe` blocks
- Use descriptive test names
- Keep tests focused and isolated
- Follow AAA pattern (Arrange, Act, Assert)

### Test Data
- Use factories for test data generation
- Keep test data minimal and focused
- Use realistic but not real data
- Avoid hardcoded IDs or dates

### Assertions
- Use specific assertions (`toHaveTextContent` vs `toBeTruthy`)
- Test user-visible behavior, not implementation details
- Prefer `screen.getByRole` over `getByTestId`
- Use `waitFor` for async assertions

### Maintenance
- Update tests when requirements change
- Remove obsolete tests
- Refactor common test patterns
- Keep test utilities up to date

## Troubleshooting

### Common Test Failures
1. **Element not found**: Check if element is rendered conditionally
2. **Async timeout**: Increase timeout or use proper async utilities
3. **Mock not working**: Verify mock is set up before component render
4. **State not updating**: Use `waitFor` for state changes

### Performance Issues
1. **Slow tests**: Check for unnecessary re-renders or large datasets
2. **Memory leaks**: Ensure proper cleanup of subscriptions/timers
3. **Flaky tests**: Add proper waits and avoid race conditions

### E2E Test Issues
1. **Element not visible**: Check viewport size and element positioning
2. **Timing issues**: Use Playwright's auto-waiting features
3. **Network issues**: Mock network requests consistently
4. **Browser differences**: Test across multiple browsers