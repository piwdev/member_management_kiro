"""
Utility functions for the asset management system.
"""

import uuid
from django.utils import timezone
from datetime import timedelta


def generate_unique_id():
    """Generate a unique UUID string."""
    return str(uuid.uuid4())


def is_license_expiring_soon(expiry_date, days_threshold=30):
    """
    Check if a license is expiring within the specified number of days.
    
    Args:
        expiry_date: The license expiry date
        days_threshold: Number of days to check (default: 30)
    
    Returns:
        bool: True if license expires within threshold, False otherwise
    """
    if not expiry_date:
        return False
    
    threshold_date = timezone.now().date() + timedelta(days=days_threshold)
    return expiry_date <= threshold_date


def calculate_license_cost(license_obj, usage_count=None):
    """
    Calculate the cost of a license based on its pricing model.
    
    Args:
        license_obj: License object with pricing information
        usage_count: Number of licenses in use (optional)
    
    Returns:
        dict: Cost breakdown with monthly, yearly, and total costs
    """
    if usage_count is None:
        usage_count = license_obj.total_count - license_obj.available_count
    
    unit_price = float(license_obj.unit_price)
    
    if license_obj.pricing_model == 'MONTHLY':
        monthly_cost = unit_price * usage_count
        yearly_cost = monthly_cost * 12
        total_cost = monthly_cost  # Current month cost
    elif license_obj.pricing_model == 'YEARLY':
        yearly_cost = unit_price * usage_count
        monthly_cost = yearly_cost / 12
        total_cost = yearly_cost  # Current year cost
    else:  # PERPETUAL
        total_cost = unit_price * usage_count
        monthly_cost = 0
        yearly_cost = 0
    
    return {
        'monthly_cost': round(monthly_cost, 2),
        'yearly_cost': round(yearly_cost, 2),
        'total_cost': round(total_cost, 2),
        'usage_count': usage_count,
        'pricing_model': license_obj.pricing_model
    }