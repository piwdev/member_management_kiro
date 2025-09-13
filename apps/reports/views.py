"""
Report views for the asset management system.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.utils import timezone
from common.permissions import IsAdminOrReadOnly
from .services import ReportService
from .serializers import (
    UsageStatsSerializer,
    InventoryStatusSerializer,
    CostAnalysisSerializer,
    UsageReportDataSerializer,
    InventoryReportDataSerializer,
    CostReportDataSerializer,
    ExportRequestSerializer
)
import csv
import json


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrReadOnly])
def usage_statistics(request):
    """
    Get usage statistics report with department, position, and period analysis.
    
    Query Parameters:
    - department: Filter by department (optional)
    - position: Filter by position (optional)
    - start_date: Start date for analysis (YYYY-MM-DD, optional)
    - end_date: End date for analysis (YYYY-MM-DD, optional)
    """
    # Validate query parameters
    serializer = UsageStatsSerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid parameters', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get report data
        filters = serializer.validated_data
        report_data = ReportService.get_usage_statistics(filters)
        
        # Serialize response
        response_serializer = UsageReportDataSerializer(report_data)
        
        return Response({
            'success': True,
            'data': response_serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to generate usage statistics', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrReadOnly])
def inventory_status(request):
    """
    Get inventory status report with utilization rates and shortage predictions.
    
    Query Parameters:
    - device_type: Filter by device type (optional)
    - software_name: Filter by software name (optional)
    """
    # Validate query parameters
    serializer = InventoryStatusSerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid parameters', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get report data
        filters = serializer.validated_data
        report_data = ReportService.get_inventory_status(filters)
        
        # Serialize response
        response_serializer = InventoryReportDataSerializer(report_data)
        
        return Response({
            'success': True,
            'data': response_serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to generate inventory status', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrReadOnly])
def department_usage(request):
    """
    Get detailed usage statistics by department.
    
    Query Parameters:
    - start_date: Start date for analysis (YYYY-MM-DD, optional)
    - end_date: End date for analysis (YYYY-MM-DD, optional)
    """
    try:
        filters = {
            'start_date': request.query_params.get('start_date'),
            'end_date': request.query_params.get('end_date')
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        report_data = ReportService.get_usage_statistics(filters)
        
        # Extract department-specific data
        department_data = {
            'department_stats': report_data['department_stats'],
            'period_summary': report_data['period_summary'],
            'generated_at': report_data['generated_at']
        }
        
        return Response({
            'success': True,
            'data': department_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to generate department usage report', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrReadOnly])
def cost_analysis(request):
    """
    Get cost analysis report with department costs and software cost trends.
    
    Query Parameters:
    - department: Filter by department (optional)
    - start_date: Start date for analysis (YYYY-MM-DD, optional)
    - end_date: End date for analysis (YYYY-MM-DD, optional)
    """
    # Validate query parameters
    serializer = CostAnalysisSerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid parameters', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get report data
        filters = serializer.validated_data
        report_data = ReportService.get_cost_analysis(filters)
        
        # Serialize response
        response_serializer = CostReportDataSerializer(report_data)
        
        return Response({
            'success': True,
            'data': response_serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to generate cost analysis', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrReadOnly])
def position_usage(request):
    """
    Get detailed usage statistics by position.
    
    Query Parameters:
    - start_date: Start date for analysis (YYYY-MM-DD, optional)
    - end_date: End date for analysis (YYYY-MM-DD, optional)
    """
    try:
        filters = {
            'start_date': request.query_params.get('start_date'),
            'end_date': request.query_params.get('end_date')
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        report_data = ReportService.get_usage_statistics(filters)
        
        # Extract position-specific data
        position_data = {
            'position_stats': report_data['position_stats'],
            'period_summary': report_data['period_summary'],
            'generated_at': report_data['generated_at']
        }
        
        return Response({
            'success': True,
            'data': position_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to generate position usage report', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOrReadOnly])
def export_report(request):
    """
    Export report data in CSV or PDF format.
    
    Request Body:
    {
        "format": "csv" | "pdf",
        "report_type": "usage_stats" | "inventory_status",
        "filters": {...}
    }
    """
    # Validate request data
    serializer = ExportRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid request data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        export_format = serializer.validated_data['format']
        report_type = serializer.validated_data['report_type']
        filters = serializer.validated_data.get('filters', {})
        
        # Generate report data
        if report_type == 'usage_stats':
            report_data = ReportService.get_usage_statistics(filters)
        elif report_type == 'inventory_status':
            report_data = ReportService.get_inventory_status(filters)
        elif report_type == 'cost_analysis':
            report_data = ReportService.get_cost_analysis(filters)
        else:
            return Response(
                {'error': 'Invalid report type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Export based on format
        if export_format == 'csv':
            return _export_csv(report_data, report_type)
        elif export_format == 'pdf':
            return _export_pdf(report_data, report_type)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to export report', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _export_csv(report_data, report_type):
    """Export report data as CSV."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_{timestamp}.csv"'
    
    writer = csv.writer(response)
    
    if report_type == 'usage_stats':
        # Write usage statistics CSV
        writer.writerow(['レポート種別', '利用状況統計'])
        writer.writerow(['生成日時', report_data['generated_at']])
        writer.writerow([])
        
        # Department statistics
        writer.writerow(['部署別統計'])
        writer.writerow(['部署', '社員数', '端末割当数', 'ライセンス割当数', '社員あたり平均端末数', '社員あたり平均ライセンス数'])
        for dept, stats in report_data['department_stats'].items():
            writer.writerow([
                dept,
                stats['employee_count'],
                stats['device_assignments'],
                stats['license_assignments'],
                stats['avg_devices_per_employee'],
                stats['avg_licenses_per_employee']
            ])
        
        writer.writerow([])
        
        # Position statistics
        writer.writerow(['役職別統計'])
        writer.writerow(['役職', '社員数', '端末割当数', 'ライセンス割当数', '社員あたり平均端末数', '社員あたり平均ライセンス数'])
        for pos, stats in report_data['position_stats'].items():
            writer.writerow([
                pos,
                stats['employee_count'],
                stats['device_assignments'],
                stats['license_assignments'],
                stats['avg_devices_per_employee'],
                stats['avg_licenses_per_employee']
            ])
    
    elif report_type == 'inventory_status':
        # Write inventory status CSV
        writer.writerow(['レポート種別', '在庫状況'])
        writer.writerow(['生成日時', report_data['generated_at']])
        writer.writerow([])
        
        # Device inventory
        writer.writerow(['端末在庫'])
        writer.writerow(['種別', '総数', '利用可能', '貸出中', '修理中'])
        for item in report_data['device_inventory']['type_breakdown']:
            writer.writerow([
                item['type'],
                item['total'],
                item['available'],
                item['assigned'],
                item['maintenance']
            ])
        
        writer.writerow([])
        
        # License inventory
        writer.writerow(['ライセンス在庫'])
        writer.writerow(['ソフトウェア名', 'ライセンス種別', '総数', '使用中', '利用可能', '利用率(%)'])
        for item in report_data['license_inventory']['license_details']:
            writer.writerow([
                item['software_name'],
                item['license_type'],
                item['total_count'],
                item['used_count'],
                item['available_count'],
                item['utilization_percentage']
            ])
    
    elif report_type == 'cost_analysis':
        # Write cost analysis CSV
        writer.writerow(['レポート種別', 'コスト分析'])
        writer.writerow(['生成日時', report_data['generated_at']])
        writer.writerow([])
        
        # Department costs
        writer.writerow(['部署別コスト'])
        writer.writerow(['部署', '社員数', 'ライセンス割当数', '月額コスト', '年額コスト', '社員あたり平均コスト'])
        for dept, costs in report_data['department_costs'].items():
            writer.writerow([
                dept,
                costs['employee_count'],
                costs['license_assignments'],
                costs['monthly_cost'],
                costs['yearly_cost'],
                costs['avg_cost_per_employee']
            ])
        
        writer.writerow([])
        
        # Software costs
        writer.writerow(['ソフトウェア別コスト'])
        writer.writerow(['ソフトウェア', '総ライセンス数', '使用中', '利用率(%)', '課金体系', '単価', '月額コスト', '年額コスト'])
        for software, costs in report_data['software_costs'].items():
            writer.writerow([
                software,
                costs['total_licenses'],
                costs['used_licenses'],
                costs['utilization_percentage'],
                costs['pricing_model'],
                costs['unit_price'],
                costs['monthly_cost'],
                costs['yearly_cost']
            ])
    
    return response


def _export_pdf(report_data, report_type):
    """Export report data as PDF."""
    # For now, return JSON data as PDF is complex to implement
    # In a real implementation, you would use libraries like reportlab or weasyprint
    response = HttpResponse(content_type='application/json')
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_{timestamp}.json"'
    
    # Return formatted JSON for now
    response.write(json.dumps(report_data, indent=2, ensure_ascii=False, default=str))
    return response
