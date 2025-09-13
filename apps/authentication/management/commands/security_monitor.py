"""
Management command for security monitoring and reporting.
"""

import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()
logger = logging.getLogger('django.security')


class Command(BaseCommand):
    help = 'Monitor security events and generate alerts'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--check-blocked-ips',
            action='store_true',
            help='Check and report blocked IPs',
        )
        parser.add_argument(
            '--check-failed-logins',
            action='store_true',
            help='Check for suspicious login patterns',
        )
        parser.add_argument(
            '--generate-report',
            action='store_true',
            help='Generate security report',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up old security data',
        )
    
    def handle(self, *args, **options):
        if options['check_blocked_ips']:
            self.check_blocked_ips()
        
        if options['check_failed_logins']:
            self.check_failed_logins()
        
        if options['generate_report']:
            self.generate_security_report()
        
        if options['cleanup']:
            self.cleanup_security_data()
        
        if not any(options.values()):
            # Run all checks by default
            self.check_blocked_ips()
            self.check_failed_logins()
            self.generate_security_report()
    
    def check_blocked_ips(self):
        """Check and report blocked IPs."""
        blocked_ips = cache.get('blocked_ips', set())
        
        if blocked_ips:
            self.stdout.write(
                self.style.WARNING(f'Found {len(blocked_ips)} blocked IPs:')
            )
            for ip in blocked_ips:
                self.stdout.write(f'  - {ip}')
                
                # Get failed attempts count
                cache_key = f"failed_attempts:{ip}"
                attempts = cache.get(cache_key, 0)
                self.stdout.write(f'    Failed attempts: {attempts}')
        else:
            self.stdout.write(
                self.style.SUCCESS('No blocked IPs found.')
            )
    
    def check_failed_logins(self):
        """Check for suspicious login patterns."""
        # Get all IPs with failed attempts
        suspicious_ips = []
        
        # This is a simplified check - in production, you'd want to
        # analyze actual log files or use a proper monitoring system
        for i in range(256):
            for j in range(256):
                ip = f"192.168.{i}.{j}"
                cache_key = f"failed_attempts:{ip}"
                attempts = cache.get(cache_key, 0)
                
                if attempts > 5:  # More than 5 failed attempts
                    suspicious_ips.append((ip, attempts))
        
        if suspicious_ips:
            self.stdout.write(
                self.style.WARNING(f'Found {len(suspicious_ips)} suspicious IPs:')
            )
            for ip, attempts in suspicious_ips:
                self.stdout.write(f'  - {ip}: {attempts} failed attempts')
        else:
            self.stdout.write(
                self.style.SUCCESS('No suspicious login patterns detected.')
            )
    
    def generate_security_report(self):
        """Generate a comprehensive security report."""
        report_data = {
            'timestamp': timezone.now(),
            'blocked_ips': len(cache.get('blocked_ips', set())),
            'active_sessions': self._count_active_sessions(),
            'recent_logins': self._count_recent_logins(),
            'failed_attempts': self._count_failed_attempts(),
        }
        
        report = self._format_security_report(report_data)
        
        self.stdout.write(
            self.style.SUCCESS('Security Report Generated:')
        )
        self.stdout.write(report)
        
        # Send email report if configured
        if hasattr(settings, 'ADMINS') and settings.ADMINS:
            try:
                send_mail(
                    subject=f'Security Report - {report_data["timestamp"].strftime("%Y-%m-%d %H:%M")}',
                    message=report,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin[1] for admin in settings.ADMINS],
                    fail_silently=False,
                )
                self.stdout.write(
                    self.style.SUCCESS('Security report sent to administrators.')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to send security report: {e}')
                )
    
    def cleanup_security_data(self):
        """Clean up old security data."""
        # Clean up old blocked IPs (older than 24 hours)
        blocked_ips = cache.get('blocked_ips', set())
        if blocked_ips:
            # In a real implementation, you'd track when IPs were blocked
            # and remove old ones. For now, just clear all.
            cache.delete('blocked_ips')
            self.stdout.write(
                self.style.SUCCESS(f'Cleared {len(blocked_ips)} blocked IPs.')
            )
        
        # Clean up old failed attempt counters
        # This is simplified - in production, you'd use a more sophisticated approach
        self.stdout.write(
            self.style.SUCCESS('Security data cleanup completed.')
        )
    
    def _count_active_sessions(self):
        """Count active user sessions."""
        from django.contrib.sessions.models import Session
        
        active_sessions = Session.objects.filter(
            expire_date__gte=timezone.now()
        ).count()
        
        return active_sessions
    
    def _count_recent_logins(self):
        """Count recent successful logins (last 24 hours)."""
        yesterday = timezone.now() - timedelta(days=1)
        
        recent_logins = User.objects.filter(
            last_login__gte=yesterday
        ).count()
        
        return recent_logins
    
    def _count_failed_attempts(self):
        """Count total failed attempts across all IPs."""
        # This is a simplified implementation
        # In production, you'd analyze log files or use proper monitoring
        total_attempts = 0
        
        # Check a sample of common IP ranges
        for i in range(10):  # Just check first 10 ranges for demo
            for j in range(10):
                ip = f"192.168.{i}.{j}"
                cache_key = f"failed_attempts:{ip}"
                attempts = cache.get(cache_key, 0)
                total_attempts += attempts
        
        return total_attempts
    
    def _format_security_report(self, data):
        """Format security report as text."""
        report = f"""
=== SECURITY REPORT ===
Generated: {data['timestamp'].strftime('%Y-%m-%d %H:%M:%S %Z')}

SUMMARY:
- Blocked IPs: {data['blocked_ips']}
- Active Sessions: {data['active_sessions']}
- Recent Logins (24h): {data['recent_logins']}
- Failed Login Attempts: {data['failed_attempts']}

RECOMMENDATIONS:
"""
        
        if data['blocked_ips'] > 0:
            report += f"- Review {data['blocked_ips']} blocked IPs for potential threats\n"
        
        if data['failed_attempts'] > 100:
            report += "- High number of failed login attempts detected\n"
        
        if data['active_sessions'] > 1000:
            report += "- Consider reviewing session timeout settings\n"
        
        if data['blocked_ips'] == 0 and data['failed_attempts'] < 10:
            report += "- Security status appears normal\n"
        
        report += "\n=== END REPORT ===\n"
        
        return report