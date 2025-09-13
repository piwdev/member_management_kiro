"""
Management command to create test users for development.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test users for development and testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--admin',
            action='store_true',
            help='Create admin user only',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Create all test users',
        )
    
    def handle(self, *args, **options):
        """Create test users."""
        
        if options['admin'] or options['all']:
            self.create_admin_user()
        
        if options['all']:
            self.create_test_users()
        
        self.stdout.write(
            self.style.SUCCESS('Test users created successfully!')
        )
    
    def create_admin_user(self):
        """Create admin user."""
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@company.com',
                password='admin123',
                first_name='管理者',
                last_name='システム',
                employee_id='ADMIN001',
                department='IT部',
                position='システム管理者',
                location='TOKYO',
                hire_date=date(2020, 1, 1)
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created admin user: {admin_user.username}')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Admin user already exists')
            )
    
    def create_test_users(self):
        """Create test users for different roles."""
        
        test_users = [
            {
                'username': 'manager_tokyo',
                'email': 'manager.tokyo@company.com',
                'password': 'manager123',
                'first_name': '太郎',
                'last_name': '田中',
                'employee_id': 'MGR001',
                'department': '営業部',
                'position': '部長',
                'location': 'TOKYO',
                'hire_date': date(2018, 4, 1),
                'is_staff': True
            },
            {
                'username': 'manager_okinawa',
                'email': 'manager.okinawa@company.com',
                'password': 'manager123',
                'first_name': '花子',
                'last_name': '佐藤',
                'employee_id': 'MGR002',
                'department': '開発部',
                'position': '部長',
                'location': 'OKINAWA',
                'hire_date': date(2019, 4, 1),
                'is_staff': True
            },
            {
                'username': 'employee_tokyo',
                'email': 'employee.tokyo@company.com',
                'password': 'employee123',
                'first_name': '次郎',
                'last_name': '鈴木',
                'employee_id': 'EMP001',
                'department': '営業部',
                'position': '主任',
                'location': 'TOKYO',
                'hire_date': date(2020, 4, 1)
            },
            {
                'username': 'employee_okinawa',
                'email': 'employee.okinawa@company.com',
                'password': 'employee123',
                'first_name': '美咲',
                'last_name': '高橋',
                'employee_id': 'EMP002',
                'department': '開発部',
                'position': 'エンジニア',
                'location': 'OKINAWA',
                'hire_date': date(2021, 4, 1)
            },
            {
                'username': 'remote_worker',
                'email': 'remote@company.com',
                'password': 'remote123',
                'first_name': '健太',
                'last_name': '山田',
                'employee_id': 'RMT001',
                'department': 'デザイン部',
                'position': 'デザイナー',
                'location': 'REMOTE',
                'hire_date': date(2022, 4, 1)
            }
        ]
        
        for user_data in test_users:
            username = user_data['username']
            
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(**user_data)
                self.stdout.write(
                    self.style.SUCCESS(f'Created user: {username}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'User {username} already exists')
                )