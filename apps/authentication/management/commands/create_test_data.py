"""
Management command to create comprehensive test data for the asset management system.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import uuid

from apps.employees.models import Employee, EmployeeHistory
from apps.devices.models import Device, DeviceAssignment
from apps.licenses.models import License, LicenseAssignment
from apps.permissions.models import PermissionPolicy, PermissionOverride
from apps.dashboard.models import Notification

User = get_user_model()


class Command(BaseCommand):
    help = 'Create comprehensive test data for the asset management system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing test data before creating new data',
        )

    def handle(self, *args, **options):
        if options['clean']:
            self.stdout.write('Cleaning existing test data...')
            self.clean_test_data()

        self.stdout.write('Creating test data...')
        
        # Create users and employees
        users_employees = self.create_users_and_employees()
        
        # Create devices
        devices = self.create_devices(users_employees['admin'])
        
        # Create licenses
        licenses = self.create_licenses(users_employees['admin'])
        
        # Create permission policies
        policies = self.create_permission_policies(users_employees['admin'])
        
        # Create assignments
        self.create_device_assignments(devices, users_employees, users_employees['admin'])
        self.create_license_assignments(licenses, users_employees, users_employees['admin'])
        
        # Create permission overrides
        self.create_permission_overrides(users_employees, users_employees['admin'])
        
        # Create notifications
        self.create_notifications(users_employees)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created comprehensive test data')
        )

    def clean_test_data(self):
        """Clean existing test data."""
        # Delete in reverse dependency order
        LicenseAssignment.objects.all().delete()
        DeviceAssignment.objects.all().delete()
        PermissionOverride.objects.all().delete()
        PermissionPolicy.objects.all().delete()
        License.objects.all().delete()
        Device.objects.all().delete()
        EmployeeHistory.objects.all().delete()
        Employee.objects.all().delete()
        Notification.objects.all().delete()
        User.objects.filter(username__startswith='test_').delete()

    def create_users_and_employees(self):
        """Create test users and employees."""
        users_employees = {}
        
        # Create admin user
        admin_user = User.objects.create_user(
            username='test_admin',
            email='admin@testcompany.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            employee_id='ADMIN001',
            department='IT',
            position='System Administrator',
            location='TOKYO',
            is_staff=True,
            is_superuser=True
        )
        users_employees['admin'] = admin_user

        # Create test employees with different roles and departments
        employee_data = [
            {
                'username': 'test_dev1',
                'email': 'dev1@testcompany.com',
                'employee_id': 'DEV001',
                'name': '田中太郎',
                'name_kana': 'タナカタロウ',
                'department': '開発部',
                'position': 'シニアエンジニア',
                'location': 'TOKYO',
                'hire_date': date(2022, 4, 1),
            },
            {
                'username': 'test_dev2',
                'email': 'dev2@testcompany.com',
                'employee_id': 'DEV002',
                'name': '佐藤花子',
                'name_kana': 'サトウハナコ',
                'department': '開発部',
                'position': 'エンジニア',
                'location': 'OKINAWA',
                'hire_date': date(2023, 1, 15),
            },
            {
                'username': 'test_sales1',
                'email': 'sales1@testcompany.com',
                'employee_id': 'SALES001',
                'name': '山田次郎',
                'name_kana': 'ヤマダジロウ',
                'department': '営業部',
                'position': 'マネージャー',
                'location': 'TOKYO',
                'hire_date': date(2021, 10, 1),
            },
            {
                'username': 'test_sales2',
                'email': 'sales2@testcompany.com',
                'employee_id': 'SALES002',
                'name': '鈴木美咲',
                'name_kana': 'スズキミサキ',
                'department': '営業部',
                'position': '営業',
                'location': 'REMOTE',
                'hire_date': date(2023, 6, 1),
            },
            {
                'username': 'test_hr1',
                'email': 'hr1@testcompany.com',
                'employee_id': 'HR001',
                'name': '高橋健一',
                'name_kana': 'タカハシケンイチ',
                'department': '人事部',
                'position': 'マネージャー',
                'location': 'TOKYO',
                'hire_date': date(2020, 4, 1),
            },
        ]

        for emp_data in employee_data:
            # Create user
            user = User.objects.create_user(
                username=emp_data['username'],
                email=emp_data['email'],
                password='testpass123',
                first_name=emp_data['name'].split()[0] if ' ' in emp_data['name'] else emp_data['name'][:2],
                last_name=emp_data['name'].split()[1] if ' ' in emp_data['name'] else emp_data['name'][2:],
                employee_id=emp_data['employee_id'],
                department=emp_data['department'],
                position=emp_data['position'],
                location=emp_data['location']
            )
            
            # Create employee
            employee = Employee.objects.create(
                user=user,
                employee_id=emp_data['employee_id'],
                name=emp_data['name'],
                name_kana=emp_data['name_kana'],
                email=emp_data['email'],
                department=emp_data['department'],
                position=emp_data['position'],
                location=emp_data['location'],
                hire_date=emp_data['hire_date'],
                phone_number=f"090-{emp_data['employee_id'][-3:]}-{emp_data['employee_id'][-3:]}",
                created_by=admin_user
            )
            
            users_employees[emp_data['username']] = user
            users_employees[f"{emp_data['username']}_employee"] = employee

        return users_employees

    def create_devices(self, admin_user):
        """Create test devices."""
        devices = []
        
        device_data = [
            {
                'type': 'LAPTOP',
                'manufacturer': 'Dell',
                'model': 'Latitude 5520',
                'serial_number': 'DL001',
                'purchase_date': date(2023, 1, 15),
                'warranty_expiry': date(2026, 1, 15),
                'specifications': {
                    'cpu': 'Intel Core i7-1165G7',
                    'ram': '16GB',
                    'storage': '512GB SSD',
                    'display': '15.6" FHD'
                }
            },
            {
                'type': 'LAPTOP',
                'manufacturer': 'Apple',
                'model': 'MacBook Pro',
                'serial_number': 'MBP001',
                'purchase_date': date(2023, 3, 1),
                'warranty_expiry': date(2026, 3, 1),
                'specifications': {
                    'cpu': 'Apple M2',
                    'ram': '16GB',
                    'storage': '512GB SSD',
                    'display': '14" Retina'
                }
            },
            {
                'type': 'DESKTOP',
                'manufacturer': 'HP',
                'model': 'EliteDesk 800',
                'serial_number': 'HP001',
                'purchase_date': date(2022, 12, 1),
                'warranty_expiry': date(2025, 12, 1),
                'specifications': {
                    'cpu': 'Intel Core i5-12500',
                    'ram': '32GB',
                    'storage': '1TB SSD'
                }
            },
            {
                'type': 'TABLET',
                'manufacturer': 'Apple',
                'model': 'iPad Pro',
                'serial_number': 'IPAD001',
                'purchase_date': date(2023, 2, 15),
                'warranty_expiry': date(2025, 2, 15),
                'specifications': {
                    'cpu': 'Apple M2',
                    'ram': '8GB',
                    'storage': '256GB',
                    'display': '12.9" Liquid Retina'
                }
            },
            {
                'type': 'SMARTPHONE',
                'manufacturer': 'Samsung',
                'model': 'Galaxy S23',
                'serial_number': 'SAM001',
                'purchase_date': date(2023, 4, 1),
                'warranty_expiry': date(2025, 4, 1),
                'specifications': {
                    'cpu': 'Snapdragon 8 Gen 2',
                    'ram': '8GB',
                    'storage': '256GB'
                }
            },
        ]

        for device_info in device_data:
            device = Device.objects.create(
                type=device_info['type'],
                manufacturer=device_info['manufacturer'],
                model=device_info['model'],
                serial_number=device_info['serial_number'],
                purchase_date=device_info['purchase_date'],
                warranty_expiry=device_info['warranty_expiry'],
                specifications=device_info['specifications'],
                created_by=admin_user
            )
            devices.append(device)

        return devices

    def create_licenses(self, admin_user):
        """Create test licenses."""
        licenses = []
        
        license_data = [
            {
                'software_name': 'Microsoft Office 365',
                'license_type': 'Business Premium',
                'total_count': 50,
                'available_count': 35,
                'expiry_date': date(2024, 12, 31),
                'pricing_model': 'MONTHLY',
                'unit_price': Decimal('1500.00'),
                'vendor_name': 'Microsoft',
                'description': 'Office 365 Business Premium subscription'
            },
            {
                'software_name': 'Adobe Creative Suite',
                'license_type': 'All Apps',
                'total_count': 10,
                'available_count': 7,
                'expiry_date': date(2024, 6, 30),
                'pricing_model': 'MONTHLY',
                'unit_price': Decimal('6000.00'),
                'vendor_name': 'Adobe',
                'description': 'Adobe Creative Cloud All Apps subscription'
            },
            {
                'software_name': 'JetBrains IntelliJ IDEA',
                'license_type': 'Ultimate',
                'total_count': 15,
                'available_count': 10,
                'expiry_date': date(2024, 8, 15),
                'pricing_model': 'YEARLY',
                'unit_price': Decimal('60000.00'),
                'vendor_name': 'JetBrains',
                'description': 'IntelliJ IDEA Ultimate annual license'
            },
            {
                'software_name': 'Slack',
                'license_type': 'Pro',
                'total_count': 100,
                'available_count': 85,
                'expiry_date': date(2024, 11, 30),
                'pricing_model': 'MONTHLY',
                'unit_price': Decimal('850.00'),
                'vendor_name': 'Slack Technologies',
                'description': 'Slack Pro subscription'
            },
            {
                'software_name': 'AutoCAD',
                'license_type': 'Standard',
                'total_count': 5,
                'available_count': 5,
                'expiry_date': date(2025, 3, 31),
                'pricing_model': 'YEARLY',
                'unit_price': Decimal('200000.00'),
                'vendor_name': 'Autodesk',
                'description': 'AutoCAD Standard annual license'
            },
            {
                'software_name': 'Zoom',
                'license_type': 'Pro',
                'total_count': 25,
                'available_count': 20,
                'expiry_date': date(2024, 2, 28),  # Expiring soon
                'pricing_model': 'MONTHLY',
                'unit_price': Decimal('2000.00'),
                'vendor_name': 'Zoom Video Communications',
                'description': 'Zoom Pro subscription'
            },
        ]

        for license_info in license_data:
            license = License.objects.create(
                software_name=license_info['software_name'],
                license_type=license_info['license_type'],
                total_count=license_info['total_count'],
                available_count=license_info['available_count'],
                expiry_date=license_info['expiry_date'],
                pricing_model=license_info['pricing_model'],
                unit_price=license_info['unit_price'],
                vendor_name=license_info['vendor_name'],
                description=license_info['description'],
                created_by=admin_user
            )
            licenses.append(license)

        return licenses

    def create_permission_policies(self, admin_user):
        """Create test permission policies."""
        policies = []
        
        # Department policies
        dept_policies = [
            {
                'name': '開発部ポリシー',
                'policy_type': 'DEPARTMENT',
                'target_department': '開発部',
                'priority': 2,
                'allowed_device_types': ['LAPTOP', 'DESKTOP', 'TABLET'],
                'allowed_software': ['Microsoft Office 365', 'JetBrains IntelliJ IDEA', 'Adobe Creative Suite'],
                'max_devices_per_type': {'LAPTOP': 2, 'DESKTOP': 1, 'TABLET': 1}
            },
            {
                'name': '営業部ポリシー',
                'policy_type': 'DEPARTMENT',
                'target_department': '営業部',
                'priority': 2,
                'allowed_device_types': ['LAPTOP', 'TABLET', 'SMARTPHONE'],
                'allowed_software': ['Microsoft Office 365', 'Slack', 'Zoom'],
                'max_devices_per_type': {'LAPTOP': 1, 'TABLET': 1, 'SMARTPHONE': 1}
            },
            {
                'name': '人事部ポリシー',
                'policy_type': 'DEPARTMENT',
                'target_department': '人事部',
                'priority': 2,
                'allowed_device_types': ['LAPTOP', 'DESKTOP'],
                'allowed_software': ['Microsoft Office 365', 'Slack'],
                'max_devices_per_type': {'LAPTOP': 1, 'DESKTOP': 1}
            }
        ]

        for policy_data in dept_policies:
            policy = PermissionPolicy.objects.create(
                name=policy_data['name'],
                policy_type=policy_data['policy_type'],
                target_department=policy_data['target_department'],
                priority=policy_data['priority'],
                allowed_device_types=policy_data['allowed_device_types'],
                allowed_software=policy_data['allowed_software'],
                max_devices_per_type=policy_data['max_devices_per_type'],
                created_by=admin_user
            )
            policies.append(policy)

        # Position policies
        pos_policies = [
            {
                'name': 'マネージャーポリシー',
                'policy_type': 'POSITION',
                'target_position': 'マネージャー',
                'priority': 1,
                'allowed_device_types': ['LAPTOP', 'DESKTOP', 'TABLET', 'SMARTPHONE'],
                'max_devices_per_type': {'LAPTOP': 2, 'DESKTOP': 1, 'TABLET': 1, 'SMARTPHONE': 1}
            }
        ]

        for policy_data in pos_policies:
            policy = PermissionPolicy.objects.create(
                name=policy_data['name'],
                policy_type=policy_data['policy_type'],
                target_position=policy_data['target_position'],
                priority=policy_data['priority'],
                allowed_device_types=policy_data['allowed_device_types'],
                max_devices_per_type=policy_data['max_devices_per_type'],
                created_by=admin_user
            )
            policies.append(policy)

        return policies

    def create_device_assignments(self, devices, users_employees, admin_user):
        """Create test device assignments."""
        assignments = []
        
        # Assign laptop to dev1
        if len(devices) > 0:
            assignment = DeviceAssignment.objects.create(
                device=devices[0],  # Dell Latitude
                employee=users_employees['test_dev1_employee'],
                assigned_date=date.today() - timedelta(days=30),
                expected_return_date=date.today() + timedelta(days=335),
                purpose='開発業務用',
                assignment_notes='新入社員用ラップトップ',
                assigned_by=admin_user,
                status='ACTIVE'
            )
            assignments.append(assignment)
            
            # Update device status
            devices[0].status = 'ASSIGNED'
            devices[0].save()

        # Assign MacBook to sales manager
        if len(devices) > 1:
            assignment = DeviceAssignment.objects.create(
                device=devices[1],  # MacBook Pro
                employee=users_employees['test_sales1_employee'],
                assigned_date=date.today() - timedelta(days=60),
                expected_return_date=date.today() + timedelta(days=305),
                purpose='営業活動・プレゼンテーション用',
                assignment_notes='マネージャー用高性能ラップトップ',
                assigned_by=admin_user,
                status='ACTIVE'
            )
            assignments.append(assignment)
            
            # Update device status
            devices[1].status = 'ASSIGNED'
            devices[1].save()

        return assignments

    def create_license_assignments(self, licenses, users_employees, admin_user):
        """Create test license assignments."""
        assignments = []
        
        # Assign Office 365 to multiple employees
        office_license = next((l for l in licenses if 'Office 365' in l.software_name), None)
        if office_license:
            employees_to_assign = [
                'test_dev1_employee',
                'test_dev2_employee', 
                'test_sales1_employee',
                'test_sales2_employee',
                'test_hr1_employee'
            ]
            
            for emp_key in employees_to_assign:
                if emp_key in users_employees:
                    assignment = LicenseAssignment.objects.create(
                        license=office_license,
                        employee=users_employees[emp_key],
                        start_date=date.today() - timedelta(days=90),
                        purpose='業務用オフィススイート',
                        assigned_by=admin_user,
                        status='ACTIVE'
                    )
                    assignments.append(assignment)

        # Assign IntelliJ to developers
        intellij_license = next((l for l in licenses if 'IntelliJ' in l.software_name), None)
        if intellij_license:
            dev_employees = ['test_dev1_employee', 'test_dev2_employee']
            
            for emp_key in dev_employees:
                if emp_key in users_employees:
                    assignment = LicenseAssignment.objects.create(
                        license=intellij_license,
                        employee=users_employees[emp_key],
                        start_date=date.today() - timedelta(days=60),
                        purpose='開発環境IDE',
                        assigned_by=admin_user,
                        status='ACTIVE'
                    )
                    assignments.append(assignment)

        # Assign Adobe Creative Suite to dev1
        adobe_license = next((l for l in licenses if 'Adobe' in l.software_name), None)
        if adobe_license and 'test_dev1_employee' in users_employees:
            assignment = LicenseAssignment.objects.create(
                license=adobe_license,
                employee=users_employees['test_dev1_employee'],
                start_date=date.today() - timedelta(days=45),
                purpose='デザイン・画像編集業務',
                assigned_by=admin_user,
                status='ACTIVE'
            )
            assignments.append(assignment)

        return assignments

    def create_permission_overrides(self, users_employees, admin_user):
        """Create test permission overrides."""
        overrides = []
        
        # Grant special access to Adobe for sales manager
        if 'test_sales1_employee' in users_employees:
            override = PermissionOverride.objects.create(
                employee=users_employees['test_sales1_employee'],
                override_type='GRANT',
                resource_type='SOFTWARE',
                resource_identifier='Adobe Creative Suite',
                effective_from=date.today() - timedelta(days=10),
                effective_until=date.today() + timedelta(days=50),
                reason='特別プロジェクト用デザインツール',
                notes='マーケティング資料作成のため',
                created_by=admin_user
            )
            overrides.append(override)

        # Restrict AutoCAD access for dev2
        if 'test_dev2_employee' in users_employees:
            override = PermissionOverride.objects.create(
                employee=users_employees['test_dev2_employee'],
                override_type='RESTRICT',
                resource_type='SOFTWARE',
                resource_identifier='AutoCAD',
                effective_from=date.today() - timedelta(days=5),
                effective_until=date.today() + timedelta(days=25),
                reason='セキュリティ研修未完了',
                notes='研修完了後に制限解除予定',
                created_by=admin_user
            )
            overrides.append(override)

        return overrides

    def create_notifications(self, users_employees):
        """Create test notifications."""
        notifications = []
        
        # License expiry notifications
        notification_data = [
            {
                'title': 'ライセンス期限切れ警告',
                'message': 'Zoomライセンスが30日以内に期限切れになります。更新手続きを行ってください。',
                'notification_type': 'LICENSE_EXPIRY',
                'priority': 'HIGH',
                'target_users': ['test_admin']
            },
            {
                'title': 'デバイス返却期限',
                'message': '貸出中のデバイスの返却予定日が近づいています。',
                'notification_type': 'DEVICE_RETURN',
                'priority': 'MEDIUM',
                'target_users': ['test_dev1', 'test_sales1']
            },
            {
                'title': 'システムメンテナンス通知',
                'message': '来週末にシステムメンテナンスを実施します。',
                'notification_type': 'SYSTEM',
                'priority': 'LOW',
                'target_users': ['test_dev1', 'test_dev2', 'test_sales1', 'test_sales2', 'test_hr1']
            }
        ]

        for notif_data in notification_data:
            for username in notif_data['target_users']:
                if username in users_employees:
                    notification = Notification.objects.create(
                        title=notif_data['title'],
                        message=notif_data['message'],
                        notification_type=notif_data['notification_type'],
                        priority=notif_data['priority'],
                        user=users_employees[username],
                        created_at=timezone.now() - timedelta(hours=2)
                    )
                    notifications.append(notification)

        return notifications