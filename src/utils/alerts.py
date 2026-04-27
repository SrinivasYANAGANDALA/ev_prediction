"""Alert and pricing logic for EV charging demand"""

import pandas as pd
import numpy as np


class AlertManager:
    """Generate alerts and pricing recommendations based on forecasts"""
    
    def __init__(self, utilization_warning=0.75, utilization_critical=0.90, 
                 price_surge_threshold=0.80):
        """
        Initialize alert manager.
        
        Args:
            utilization_warning: Threshold for warning (0-1)
            utilization_critical: Threshold for critical (0-1)
            price_surge_threshold: Threshold for price surge recommendation
        """
        self.utilization_warning = utilization_warning
        self.utilization_critical = utilization_critical
        self.price_surge_threshold = price_surge_threshold
    
    def evaluate_station(self, station_id, forecasted_demand, capacity, 
                        current_sessions=None):
        """
        Evaluate single station and generate alerts/recommendations.
        
        Args:
            station_id: ID of the station
            forecasted_demand: Predicted kWh demand
            capacity: Station capacity in kW
            current_sessions: Current active sessions (optional)
        
        Returns:
            dict: Status, alerts, and recommendations
        """
        
        # Calculate utilization as percentage of capacity
        utilization = min(forecasted_demand / capacity, 1.0)
        
        # Determine status
        if utilization >= self.utilization_critical:
            status = "critical"
            status_color = "red"
        elif utilization >= self.utilization_warning:
            status = "warning"
            status_color = "yellow"
        else:
            status = "normal"
            status_color = "green"
        
        # Generate alerts
        alerts = []
        recommendations = []
        
        if utilization >= self.utilization_critical:
            alerts.append(f"CRITICAL: Station {station_id} predicted at {utilization*100:.1f}% capacity")
            recommendations.append("Increase pricing by 30-50% to reduce demand")
            recommendations.append("Send notifications to redirect users to nearby stations")
            recommendations.append("Consider temporary closure if approaching hard limits")
        
        elif utilization >= self.utilization_warning:
            alerts.append(f"WARNING: Station {station_id} predicted at {utilization*100:.1f}% capacity")
            recommendations.append("Increase pricing by 15-25% to moderate demand")
            recommendations.append("Monitor usage closely for next 2 hours")
        
        if utilization >= self.price_surge_threshold:
            price_multiplier = 1.0 + (utilization - self.price_surge_threshold) * 2.0
            recommendations.append(f"Suggested price multiplier: {price_multiplier:.2f}x")
        
        return {
            'station_id': station_id,
            'utilization_percent': utilization * 100,
            'status': status,
            'status_color': status_color,
            'alerts': alerts,
            'recommendations': recommendations,
            'forecasted_demand': forecasted_demand,
            'capacity': capacity
        }
    
    def batch_evaluate(self, forecast_df, capacity_map):
        """
        Evaluate multiple stations at once.
        
        Args:
            forecast_df: DataFrame with columns [station_id, forecasted_demand]
            capacity_map: Dict mapping station_id to capacity
        
        Returns:
            list: List of evaluation results
        """
        
        results = []
        for _, row in forecast_df.iterrows():
            station_id = row['station_id']
            capacity = capacity_map.get(station_id, 250)  # Default 250 kW
            
            evaluation = self.evaluate_station(
                station_id=station_id,
                forecasted_demand=row['forecasted_demand'],
                capacity=capacity
            )
            results.append(evaluation)
        
        return results
    
    def get_summary(self, evaluations):
        """Get summary of all evaluations"""
        
        total_stations = len(evaluations)
        critical_stations = sum(1 for e in evaluations if e['status'] == 'critical')
        warning_stations = sum(1 for e in evaluations if e['status'] == 'warning')
        normal_stations = sum(1 for e in evaluations if e['status'] == 'normal')
        
        all_alerts = []
        all_recommendations = []
        
        for evaluation in evaluations:
            all_alerts.extend(evaluation['alerts'])
            all_recommendations.extend(evaluation['recommendations'])
        
        summary = {
            'total_stations': total_stations,
            'critical_count': critical_stations,
            'warning_count': warning_stations,
            'normal_count': normal_stations,
            'total_alerts': len(all_alerts),
            'alerts': all_alerts[:5],  # Top 5 alerts
            'unique_recommendations': list(set(all_recommendations))[:5]  # Top 5 unique
        }
        
        return summary


class PricingRecommender:
    """Generate dynamic pricing recommendations"""
    
    def __init__(self, base_price=0.50):  # $/kWh
        self.base_price = base_price
    
    def recommend_price(self, utilization):
        """
        Recommend price based on utilization.
        
        Args:
            utilization: Utilization ratio (0-1)
        
        Returns:
            float: Recommended price per kWh
        """
        
        if utilization < 0.5:
            # Encourage usage - discount
            multiplier = 0.7
        elif utilization < 0.75:
            # Normal pricing
            multiplier = 1.0
        elif utilization < 0.85:
            # Moderate surge
            multiplier = 1.25
        elif utilization < 0.95:
            # High surge
            multiplier = 1.75
        else:
            # Peak pricing
            multiplier = 2.0
        
        return self.base_price * multiplier
    
    def get_pricing_tier(self, utilization):
        """Get pricing tier name"""
        
        tiers = [
            (0.5, "Economy", "green"),
            (0.75, "Standard", "yellow"),
            (0.85, "Premium", "orange"),
            (0.95, "Peak", "red"),
            (1.0, "Critical", "darkred")
        ]
        
        for threshold, tier_name, color in reversed(tiers):
            if utilization >= threshold:
                return tier_name, color
        
        return "Economy", "green"
