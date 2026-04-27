"""Utility functions for the dashboard"""

import pandas as pd
import json


def format_timestamp(dt):
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M")


def get_station_color(utilization):
    """Get color for station based on utilization"""
    if utilization >= 0.90:
        return "critical"
    elif utilization >= 0.75:
        return "warning"
    else:
        return "normal"


def format_number(num, decimals=2):
    """Format number with decimals"""
    return round(num, decimals)


def calculate_statistics(df, column):
    """Calculate basic statistics for a column"""
    return {
        'mean': float(df[column].mean()),
        'std': float(df[column].std()),
        'min': float(df[column].min()),
        'max': float(df[column].max()),
        'median': float(df[column].median())
    }
