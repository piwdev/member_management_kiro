"""
Management command to generate security reports.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from datetime import timedelta
from apps.authentication.models import LoginAttempt

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate security reports for authentication system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to include in the report (default: 7)'
        )
        parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format (default: text)'
        )

    def handle(self, *args, **options):
        days = options['days']
        output_format = options['format']
        
        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Generate report data
        report_data = self._generate_report_data(start_date, end_date)
        
        # Output report
        if output_format == 'json':
            self._output_json_report(report_data)
        else:
            self._output_text_report(report_data, days)

    def _generate_report_data(self, start_date, end_date):
        """Generate security report data."""
        
        # Login attempts in date range
        login_attempts = LoginAttempt.objects.filter(
            timestamp__range=[start_date, end_date]
        )
        
        # Failed login attempts
        failed_attempts = login_attempts.filter(success=False)
        
        # Successful login attempts
        successful_attempts = login_attempts.filter(success=True)
        
        # Locked accounts
        locked_accounts = User.objects.filter(
            account_locked_until__isnull=False,
            account_locked_until__gt=timezone.now()
        )
        
        # Users with multiple failed attempts
        users_with_failures = User.objects.filter(
            failed_login_attempts__gt=0
        ).order_by('-failed_login_attempts')
        
        # Top IP addresses with failed attempts
        failed_ips = (
            failed_attempts
            .values('ip_address')
            .annotate(count=models.Count('ip_address'))
            .order_by('-count')[:10]
        )
        
        # Recent successful logins by IP
        recent_successful_ips = (
            successful_attempts
            .values('ip_address')
            .annotate(count=models.Count('ip_address'))
            .order_by('-count')[:10]
        )
        
        return {
            'total_login_attempts': login_attempts.count(),
            'successful_attempts': successful_attempts.count(),
            'failed_attempts': failed_attempts.count(),
            'locked_accounts': locked_accounts.count(),
            'users_with_failures': users_with_failures.count(),
            'failed_ips': list(failed_ips),
            'successful_ips': list(recent_successful_ips),
            'locked_accounts_list': list(locked_accounts.values('username', 'account_locked_until')),
            'users_with_failures_list': list(users_with_failures.values('username', 'failed_login_attempts')[:10])
        }

    def _output_text_report(self, data, days):
        """Output report in text format."""
        self.stdout.write(
            self.style.SUCCESS(f'\n=== セキュリティレポート (過去{days}日間) ===\n')
        )
        
        # Summary
        self.stdout.write('【概要】')
        self.stdout.write(f'  総ログイン試行数: {data["total_login_attempts"]}')
        self.stdout.write(f'  成功: {data["successful_attempts"]}')
        self.stdout.write(f'  失敗: {data["failed_attempts"]}')
        
        if data["total_login_attempts"] > 0:
            success_rate = (data["successful_attempts"] / data["total_login_attempts"]) * 100
            self.stdout.write(f'  成功率: {success_rate:.1f}%')
        
        self.stdout.write(f'  現在ロック中のアカウント: {data["locked_accounts"]}')
        self.stdout.write(f'  ログイン失敗履歴があるユーザー: {data["users_with_failures"]}')
        
        # Locked accounts
        if data["locked_accounts_list"]:
            self.stdout.write('\n【ロック中のアカウント】')
            for account in data["locked_accounts_list"]:
                self.stdout.write(f'  - {account["username"]} (ロック期限: {account["account_locked_until"]})')
        
        # Users with failed attempts
        if data["users_with_failures_list"]:
            self.stdout.write('\n【ログイン失敗履歴があるユーザー (上位10名)】')
            for user in data["users_with_failures_list"]:
                self.stdout.write(f'  - {user["username"]}: {user["failed_login_attempts"]}回失敗')
        
        # Failed IPs
        if data["failed_ips"]:
            self.stdout.write('\n【ログイン失敗の多いIPアドレス (上位10件)】')
            for ip_data in data["failed_ips"]:
                self.stdout.write(f'  - {ip_data["ip_address"]}: {ip_data["count"]}回失敗')
        
        # Successful IPs
        if data["successful_ips"]:
            self.stdout.write('\n【ログイン成功の多いIPアドレス (上位10件)】')
            for ip_data in data["successful_ips"]:
                self.stdout.write(f'  - {ip_data["ip_address"]}: {ip_data["count"]}回成功')
        
        self.stdout.write('')

    def _output_json_report(self, data):
        """Output report in JSON format."""
        import json
        self.stdout.write(json.dumps(data, indent=2, default=str, ensure_ascii=False))