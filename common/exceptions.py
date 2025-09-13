"""
Custom exception classes for the asset management system.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


class AssetManagementException(Exception):
    """Base exception class for asset management system."""
    pass


class LicenseNotAvailableException(AssetManagementException):
    """Raised when trying to assign a license that is not available."""
    pass


class DeviceAlreadyAssignedException(AssetManagementException):
    """Raised when trying to assign a device that is already assigned."""
    pass


class InsufficientPermissionException(AssetManagementException):
    """Raised when user doesn't have permission for the requested resource."""
    pass


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    """
    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            'error': {
                'code': response.status_code,
                'message': 'An error occurred',
                'details': response.data
            }
        }

        # Customize error messages based on exception type
        if isinstance(exc, LicenseNotAvailableException):
            custom_response_data['error']['message'] = 'License not available for assignment'
        elif isinstance(exc, DeviceAlreadyAssignedException):
            custom_response_data['error']['message'] = 'Device is already assigned to another user'
        elif isinstance(exc, InsufficientPermissionException):
            custom_response_data['error']['message'] = 'Insufficient permissions for this resource'

        response.data = custom_response_data

    return response