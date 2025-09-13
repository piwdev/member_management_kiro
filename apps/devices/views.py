"""
Views for device management API.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.exceptions import ValidationError

from .models import Device, DeviceAssignment
from .serializers import (
    DeviceSerializer,
    DeviceListSerializer,
    DeviceAssignmentSerializer,
    DeviceAssignRequestSerializer,
    DeviceReturnRequestSerializer,
    DeviceAssignmentHistorySerializer
)
from apps.employees.models import Employee
from common.permissions import IsAdminOrReadOnly


class DeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing devices.
    
    Provides CRUD operations for devices and additional actions for
    assignment and return operations.
    """
    
    queryset = Device.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return DeviceListSerializer
        return DeviceSerializer
    
    def get_queryset(self):
        """Filter devices based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by type
        device_type = self.request.query_params.get('type')
        if device_type:
            queryset = queryset.filter(type=device_type)
        
        # Filter by status
        device_status = self.request.query_params.get('status')
        if device_status:
            queryset = queryset.filter(status=device_status)
        
        # Filter by manufacturer
        manufacturer = self.request.query_params.get('manufacturer')
        if manufacturer:
            queryset = queryset.filter(manufacturer__icontains=manufacturer)
        
        # Search by serial number or model
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(serial_number__icontains=search) |
                Q(model__icontains=search) |
                Q(manufacturer__icontains=search)
            )
        
        # Filter available devices only
        available_only = self.request.query_params.get('available_only')
        if available_only and available_only.lower() == 'true':
            queryset = queryset.filter(status='AVAILABLE')
        
        return queryset
    
    def perform_create(self, serializer):
        """Set created_by when creating a device."""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Set updated_by when updating a device."""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """
        Assign device to an employee.
        
        POST /api/devices/{id}/assign/
        {
            "employee_id": "uuid",
            "assigned_date": "2023-01-01",
            "expected_return_date": "2023-12-31",
            "purpose": "Development work",
            "assignment_notes": "Optional notes"
        }
        """
        device = self.get_object()
        serializer = DeviceAssignRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                employee = Employee.objects.get(id=serializer.validated_data['employee_id'])
                
                assignment = device.assign_to_employee(
                    employee=employee,
                    assigned_date=serializer.validated_data['assigned_date'],
                    return_date=serializer.validated_data.get('expected_return_date'),
                    purpose=serializer.validated_data['purpose'],
                    assigned_by=request.user
                )
                
                # Set assignment notes if provided
                if serializer.validated_data.get('assignment_notes'):
                    assignment.assignment_notes = serializer.validated_data['assignment_notes']
                    assignment.save()
                
                assignment_serializer = DeviceAssignmentSerializer(assignment)
                return Response(assignment_serializer.data, status=status.HTTP_201_CREATED)
                
            except ValidationError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Employee.DoesNotExist:
                return Response(
                    {'error': '指定された社員が見つかりません。'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def return_device(self, request, pk=None):
        """
        Return device from current assignment.
        
        POST /api/devices/{id}/return/
        {
            "return_date": "2023-06-01",
            "return_notes": "Device returned in good condition"
        }
        """
        device = self.get_object()
        serializer = DeviceReturnRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                assignment = device.return_from_employee(
                    return_date=serializer.validated_data['return_date'],
                    returned_by=request.user,
                    notes=serializer.validated_data.get('return_notes', '')
                )
                
                assignment_serializer = DeviceAssignmentSerializer(assignment)
                return Response(assignment_serializer.data, status=status.HTTP_200_OK)
                
            except ValidationError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        """
        Get assignment history for a device.
        
        GET /api/devices/{id}/assignments/
        """
        device = self.get_object()
        assignments = device.assignments.all().order_by('-assigned_date')
        
        # Pagination
        page = self.paginate_queryset(assignments)
        if page is not None:
            serializer = DeviceAssignmentHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = DeviceAssignmentHistorySerializer(assignments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def current_assignment(self, request, pk=None):
        """
        Get current assignment for a device.
        
        GET /api/devices/{id}/current-assignment/
        """
        device = self.get_object()
        assignment = device.current_assignment
        
        if assignment:
            serializer = DeviceAssignmentSerializer(assignment)
            return Response(serializer.data)
        
        return Response(
            {'message': 'この端末は現在割り当てられていません。'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get device statistics.
        
        GET /api/devices/statistics/
        """
        total_devices = Device.objects.count()
        available_devices = Device.objects.filter(status='AVAILABLE').count()
        assigned_devices = Device.objects.filter(status='ASSIGNED').count()
        maintenance_devices = Device.objects.filter(status='MAINTENANCE').count()
        disposed_devices = Device.objects.filter(status='DISPOSED').count()
        
        # Device type breakdown
        type_stats = {}
        for choice in Device.TYPE_CHOICES:
            type_key = choice[0]
            type_label = choice[1]
            count = Device.objects.filter(type=type_key).count()
            type_stats[type_key] = {
                'label': type_label,
                'count': count
            }
        
        # Warranty status
        warranty_stats = {
            'valid': 0,
            'expiring_soon': 0,
            'expired': 0
        }
        
        for device in Device.objects.all():
            warranty_status = device.warranty_status
            if warranty_status == 'VALID':
                warranty_stats['valid'] += 1
            elif warranty_status == 'EXPIRING_SOON':
                warranty_stats['expiring_soon'] += 1
            elif warranty_status == 'EXPIRED':
                warranty_stats['expired'] += 1
        
        return Response({
            'total_devices': total_devices,
            'status_breakdown': {
                'available': available_devices,
                'assigned': assigned_devices,
                'maintenance': maintenance_devices,
                'disposed': disposed_devices
            },
            'type_breakdown': type_stats,
            'warranty_breakdown': warranty_stats
        })


class DeviceAssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing device assignments.
    
    Provides CRUD operations for device assignments and filtering capabilities.
    """
    
    queryset = DeviceAssignment.objects.all().order_by('-assigned_date')
    serializer_class = DeviceAssignmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    
    def get_queryset(self):
        """Filter assignments based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by device
        device_id = self.request.query_params.get('device_id')
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by status
        assignment_status = self.request.query_params.get('status')
        if assignment_status:
            queryset = queryset.filter(status=assignment_status)
        
        # Filter active assignments only
        active_only = self.request.query_params.get('active_only')
        if active_only and active_only.lower() == 'true':
            queryset = queryset.filter(status='ACTIVE')
        
        # Filter overdue assignments
        overdue_only = self.request.query_params.get('overdue_only')
        if overdue_only and overdue_only.lower() == 'true':
            queryset = queryset.filter(status='OVERDUE')
        
        return queryset
    
    def perform_create(self, serializer):
        """Set assigned_by when creating an assignment."""
        serializer.save(assigned_by=self.request.user)
    
    def perform_update(self, serializer):
        """Set returned_by when updating an assignment with return date."""
        instance = serializer.instance
        validated_data = serializer.validated_data
        
        # If actual_return_date is being set and returned_by is not set
        if (validated_data.get('actual_return_date') and 
            not instance.returned_by):
            serializer.save(returned_by=self.request.user)
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """
        Get overdue assignments.
        
        GET /api/device-assignments/overdue/
        """
        overdue_assignments = self.get_queryset().filter(status='OVERDUE')
        
        page = self.paginate_queryset(overdue_assignments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(overdue_assignments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_employee(self, request):
        """
        Get assignments by employee.
        
        GET /api/device-assignments/by-employee/?employee_id=uuid
        """
        employee_id = request.query_params.get('employee_id')
        if not employee_id:
            return Response(
                {'error': 'employee_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response(
                {'error': '指定された社員が見つかりません。'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        assignments = self.get_queryset().filter(employee=employee)
        
        page = self.paginate_queryset(assignments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(assignments, many=True)
        return Response(serializer.data)
