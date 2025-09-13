#!/usr/bin/env python
"""
Test runner script for the asset management system.
Provides various test running options and configurations.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asset_management.settings.test')

def run_django_tests(args):
    """Run Django tests using manage.py test."""
    cmd = ['python', 'manage.py', 'test']
    
    if args.app:
        cmd.extend(args.app)
    
    if args.verbosity:
        cmd.extend(['--verbosity', str(args.verbosity)])
    
    if args.keepdb:
        cmd.append('--keepdb')
    
    if args.parallel:
        cmd.extend(['--parallel', str(args.parallel)])
    
    if args.failfast:
        cmd.append('--failfast')
    
    if args.debug_mode:
        cmd.append('--debug-mode')
    
    return subprocess.run(cmd)

def run_pytest(args):
    """Run tests using pytest."""
    cmd = ['python', '-m', 'pytest']
    
    if args.app:
        # Convert app names to test paths
        test_paths = []
        for app in args.app:
            if '.' in app:
                # Specific test module or class
                test_paths.append(app)
            else:
                # App directory
                test_paths.append(f'apps/{app}/tests.py')
        cmd.extend(test_paths)
    
    if args.verbosity:
        if args.verbosity >= 2:
            cmd.append('-vv')
        elif args.verbosity == 1:
            cmd.append('-v')
    
    if args.failfast:
        cmd.append('-x')
    
    if args.coverage:
        cmd.extend(['--cov=apps', '--cov=common', '--cov-report=html', '--cov-report=term-missing'])
    
    if args.markers:
        cmd.extend(['-m', args.markers])
    
    if args.keyword:
        cmd.extend(['-k', args.keyword])
    
    return subprocess.run(cmd)

def run_specific_tests(args):
    """Run specific test categories."""
    if args.unit:
        print("Running unit tests...")
        return subprocess.run(['python', '-m', 'pytest', '-m', 'unit'])
    
    elif args.integration:
        print("Running integration tests...")
        return subprocess.run(['python', '-m', 'pytest', '-m', 'integration', 'tests/'])
    
    elif args.api:
        print("Running API tests...")
        return subprocess.run(['python', '-m', 'pytest', '-m', 'api'])
    
    elif args.security:
        print("Running security tests...")
        return subprocess.run(['python', '-m', 'pytest', '-m', 'security'])
    
    elif args.performance:
        print("Running performance tests...")
        return subprocess.run(['python', '-m', 'pytest', '-m', 'performance'])

def setup_test_data(args):
    """Set up test data using management commands."""
    print("Setting up test data...")
    
    # Run migrations
    subprocess.run(['python', 'manage.py', 'migrate', '--settings=asset_management.settings.test'])
    
    # Load fixtures
    subprocess.run(['python', 'manage.py', 'loaddata', 'fixtures/test_data.json', '--settings=asset_management.settings.test'])
    
    # Create additional test data
    if args.comprehensive:
        subprocess.run(['python', 'manage.py', 'create_test_data', '--settings=asset_management.settings.test'])
    
    print("Test data setup complete.")

def cleanup_test_data():
    """Clean up test data and files."""
    print("Cleaning up test data...")
    
    # Remove test database if it exists
    test_db_path = project_dir / 'test_db.sqlite3'
    if test_db_path.exists():
        test_db_path.unlink()
    
    # Remove test media files
    import shutil
    test_media_path = Path('/tmp/test_media')
    if test_media_path.exists():
        shutil.rmtree(test_media_path)
    
    test_static_path = Path('/tmp/test_static')
    if test_static_path.exists():
        shutil.rmtree(test_static_path)
    
    print("Cleanup complete.")

def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Asset Management System Test Runner')
    
    # Test runner selection
    parser.add_argument('--runner', choices=['django', 'pytest'], default='pytest',
                       help='Test runner to use (default: pytest)')
    
    # Test selection
    parser.add_argument('app', nargs='*', help='Specific apps or test modules to run')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--api', action='store_true', help='Run API tests only')
    parser.add_argument('--security', action='store_true', help='Run security tests only')
    parser.add_argument('--performance', action='store_true', help='Run performance tests only')
    
    # Test configuration
    parser.add_argument('--verbosity', '-v', type=int, choices=[0, 1, 2], default=1,
                       help='Verbosity level')
    parser.add_argument('--failfast', '-x', action='store_true',
                       help='Stop on first failure')
    parser.add_argument('--keepdb', action='store_true',
                       help='Keep test database between runs')
    parser.add_argument('--parallel', type=int,
                       help='Run tests in parallel')
    parser.add_argument('--debug-mode', action='store_true',
                       help='Enable debug mode')
    
    # Pytest specific options
    parser.add_argument('--coverage', action='store_true',
                       help='Generate coverage report')
    parser.add_argument('--markers', '-m',
                       help='Run tests matching given mark expression')
    parser.add_argument('--keyword', '-k',
                       help='Run tests matching given keyword expression')
    
    # Data management
    parser.add_argument('--setup-data', action='store_true',
                       help='Set up test data before running tests')
    parser.add_argument('--comprehensive', action='store_true',
                       help='Create comprehensive test data')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up test data and files')
    
    args = parser.parse_args()
    
    # Handle cleanup
    if args.cleanup:
        cleanup_test_data()
        return
    
    # Handle data setup
    if args.setup_data:
        setup_test_data(args)
        if not any([args.unit, args.integration, args.api, args.security, args.performance]) and not args.app:
            return
    
    # Handle specific test categories
    if any([args.unit, args.integration, args.api, args.security, args.performance]):
        result = run_specific_tests(args)
        return result.returncode
    
    # Run tests based on selected runner
    if args.runner == 'django':
        result = run_django_tests(args)
    else:
        result = run_pytest(args)
    
    return result.returncode

if __name__ == '__main__':
    sys.exit(main())