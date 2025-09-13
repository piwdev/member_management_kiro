"""
Report serializers for the asset management system.
"""

from rest_framework import serializers
from decimal import Decimal


class UsageStatsSerializer(serializers.Serializer):
    """Serializer for usage statistics report."""
    
    department = serializers.CharField(required=False, allow_blank=True)
    position = serializers.CharField(required=False, allow_blank=True)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    
    def validate(self, data):
        """Validate date range."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                "開始日は終了日より前である必要があります。"
            )
        
        return data


class InventoryStatusSerializer(serializers.Serializer):
    """Serializer for inventory status report."""
    
    device_type = serializers.CharField(required=False, allow_blank=True)
    software_name = serializers.CharField(required=False, allow_blank=True)


class CostAnalysisSerializer(serializers.Serializer):
    """Serializer for cost analysis report."""
    
    department = serializers.CharField(required=False, allow_blank=True)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    
    def validate(self, data):
        """Validate date range."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                "開始日は終了日より前である必要があります。"
            )
        
        return data


class UsageReportDataSerializer(serializers.Serializer):
    """Serializer for usage report response data."""
    
    department_stats = serializers.DictField()
    position_stats = serializers.DictField()
    device_usage = serializers.DictField()
    license_usage = serializers.DictField()
    period_summary = serializers.DictField()


class InventoryReportDataSerializer(serializers.Serializer):
    """Serializer for inventory report response data."""
    
    device_inventory = serializers.DictField()
    license_inventory = serializers.DictField()
    utilization_rates = serializers.DictField()
    shortage_predictions = serializers.DictField()


class CostReportDataSerializer(serializers.Serializer):
    """Serializer for cost analysis report response data."""
    
    department_costs = serializers.DictField()
    software_costs = serializers.DictField()
    cost_trends = serializers.DictField()
    budget_comparison = serializers.DictField()


class ExportRequestSerializer(serializers.Serializer):
    """Serializer for export request parameters."""
    
    EXPORT_FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
    ]
    
    format = serializers.ChoiceField(choices=EXPORT_FORMAT_CHOICES)
    report_type = serializers.CharField()
    filters = serializers.DictField(required=False)
