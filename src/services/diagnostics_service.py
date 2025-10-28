"""
Diagnostics Service - Handles anomaly detection and real-time scanning operations
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid
from .database_service import database_service


class DiagnosticsService:
    """Service for anomaly detection and diagnostics operations"""
    
    def __init__(self):
        self.table_name = "lakehouse_inn_catalog.voc.open_issues_diagnosis"
        self._cache = {}
        self._cache_timestamp = None
    
    def _get_placeholder_data(self) -> List[Dict]:
        """Return placeholder data when database is unavailable"""
        return [
            {'location': 'Austin, TX', 'aspect': 'WiFi Connectivity', 'severity': 'Critical', 'status': 'Open', 'open_reason': 'connectivity_issues', 'nms_open': 5.1, 'opened_at': '2024-01-12', 'response_result': None},
            {'location': 'Denver, CO', 'aspect': 'Room Cleanliness', 'severity': 'Critical', 'status': 'Open', 'open_reason': 'cleanliness_complaints', 'nms_open': 4.8, 'opened_at': '2024-01-15', 'response_result': None},
            {'location': 'Miami, FL', 'aspect': 'Staff Service', 'severity': 'Warning', 'status': 'Open', 'open_reason': 'service_delays', 'nms_open': 3.2, 'opened_at': '2024-01-14', 'response_result': None},
            {'location': 'Chicago, IL', 'aspect': 'Noise Levels', 'severity': 'Warning', 'status': 'Open', 'open_reason': 'noise_complaints', 'nms_open': 3.1, 'opened_at': '2024-01-13', 'response_result': None},
            {'location': 'Miami, FL', 'aspect': 'Amenities', 'severity': 'Good', 'status': 'Open', 'open_reason': 'amenity_concerns', 'nms_open': 2.1, 'opened_at': '2024-01-14', 'response_result': None},
            {'location': 'Austin, TX', 'aspect': 'Amenities', 'severity': 'Good', 'status': 'Open', 'open_reason': 'amenity_requests', 'nms_open': 2.0, 'opened_at': '2024-01-12', 'response_result': None},
            {'location': 'Chicago, IL', 'aspect': 'Room Cleanliness', 'severity': 'Good', 'status': 'Open', 'open_reason': 'cleanliness_feedback', 'nms_open': 1.5, 'opened_at': '2024-01-13', 'response_result': None},
            {'location': 'Denver, CO', 'aspect': 'Staff Service', 'severity': 'Good', 'status': 'Open', 'open_reason': 'service_feedback', 'nms_open': 1.2, 'opened_at': '2024-01-15', 'response_result': None},
            {'location': 'Seattle, WA', 'aspect': 'Amenities', 'severity': 'Good', 'status': 'Open', 'open_reason': 'amenity_feedback', 'nms_open': 1.1, 'opened_at': '2024-01-11', 'response_result': None},
            {'location': 'Seattle, WA', 'aspect': 'Room Cleanliness', 'severity': 'Excellent', 'status': 'Open', 'open_reason': 'minor_feedback', 'nms_open': 0.8, 'opened_at': '2024-01-11', 'response_result': None},
        ]
    
    def _get_issues_data(self) -> List[Dict]:
        """Fetch issues data from Databricks table with caching"""
        # Cache for 5 minutes
        if (self._cache_timestamp and 
            (datetime.now() - self._cache_timestamp).seconds < 300):
            return self._cache.get('issues', [])
        
        try:
            query = f"""
                SELECT 
                    location,
                    aspect,
                    severity,
                    status,
                    open_reason,
                    nms_open,
                    opened_at,
                    response_result
                FROM {self.table_name}
                WHERE status = 'Open'
                ORDER BY nms_open DESC
            """
            
            issues = database_service.query(query)
            
            # Use placeholder data if query returns None (connection failed)
            if issues is None:
                print("📊 Using placeholder data for diagnostics service")
                return self._get_placeholder_data()
            
            self._cache['issues'] = issues
            self._cache_timestamp = datetime.now()
            return issues
            
        except Exception as e:
            print(f"⚠️  Error fetching issues data: {str(e)}")
            print("📊 Using placeholder data for diagnostics service")
            return self._get_placeholder_data()
    
    def kickoff_anomaly_workspace(self) -> Dict:
        """Initiate anomaly detection workspace"""
        issues = self._get_issues_data()
        
        workspace_id = f"ws_anomaly_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Count unique properties and aspects
        unique_properties = len(set(issue.get('location', '') for issue in issues))
        unique_aspects = len(set(issue.get('aspect', '') for issue in issues))
        
        return {
            'status': 'initiated',
            'workspace_id': workspace_id,
            'message': 'Anomaly detection workspace initiated successfully',
            'estimated_completion': (datetime.now() + timedelta(minutes=15)).isoformat(),
            'properties_to_scan': unique_properties,
            'aspects_to_analyze': unique_aspects,
            'scan_type': 'comprehensive_anomaly_detection'
        }
    
    def get_scan_progress(self) -> Dict:
        """Get current scanning progress and statistics from database"""
        issues = self._get_issues_data()
        
        # Count unique properties
        unique_properties = len(set(issue.get('location', '') for issue in issues))
        
        # Count by severity
        critical_issues = sum(1 for issue in issues if issue.get('severity', '').lower() == 'critical')
        warning_issues = sum(1 for issue in issues if issue.get('severity', '').lower() == 'warning')
        total_anomalies = len(issues)
        
        return {
            'properties_scanned': f"{unique_properties} of {unique_properties}",
            'anomalies_total': total_anomalies,
            'critical_count': critical_issues,
            'warning_count': warning_issues,
            'scan_status': 'complete',
            'completion_percentage': 100.0
        }
    
    def get_scan_results(self) -> List[Dict]:
        """Get detailed scan results for all properties from database"""
        issues = self._get_issues_data()
        
        # Group issues by property
        property_issues = {}
        for issue in issues:
            location = issue.get('location', 'Unknown')
            if location not in property_issues:
                property_issues[location] = []
            property_issues[location].append(issue)
        
        results = []
        for location, issues_list in property_issues.items():
            prop_id = location.lower().replace(' ', '-').replace(',', '')
            
            # Find highest severity issue for this property
            has_critical = any(i.get('severity', '').lower() == 'critical' for i in issues_list)
            has_issues = len(issues_list) > 0
            
            # Get the highest nms_open issue
            top_issue = max(issues_list, key=lambda x: float(x.get('nms_open', 0))) if issues_list else {}
            
            result = {
                'property_id': prop_id,
                'property_name': location,
                'status': 'issue_found' if has_issues else 'complete',
                'scan_time': '0:02',
                'issues_found': has_issues
            }
            
            if has_issues:
                result.update({
                    'aspect': top_issue.get('aspect', 'Unknown'),
                    'signal': f"{top_issue.get('nms_open', 0)} negative reviews",
                    'signal_value': float(top_issue.get('nms_open', 0)),
                    'mentions': len(issues_list),
                    'mentions_change': 0,  # Would need historical data
                    'severity': top_issue.get('severity', 'warning').lower(),
                    'quick_action': f"Address {top_issue.get('aspect', 'issues')}"
                })
            
            results.append(result)
        
        return results
    
    def get_top_affected_aspects(self) -> List[str]:
        """Get the most commonly affected aspects from database"""
        issues = self._get_issues_data()
        
        # Count occurrences of each aspect
        aspect_counts = {}
        for issue in issues:
            aspect = issue.get('aspect', 'Unknown')
            aspect_counts[aspect] = aspect_counts.get(aspect, 0) + 1
        
        # Sort by count and return top 3
        sorted_aspects = sorted(aspect_counts.items(), key=lambda x: x[1], reverse=True)
        return [aspect for aspect, count in sorted_aspects[:3]]
    
    def get_recent_actions(self) -> Dict:
        """Get summary of recent actions taken"""
        issues = self._get_issues_data()
        
        # Count properties with issues
        flagged_properties = len(set(issue.get('location', '') for issue in issues))
        
        return {
            'emails_sent': 0,  # Would track in a separate table
            'tickets_opened': 0,  # Would track in a separate table
            'properties_flagged': flagged_properties,
            'last_action_time': datetime.now() - timedelta(minutes=15),
            'actions_today': len(issues)
        }
    
    def simulate_scan_progress(self) -> Dict:
        """Get current scan progress (using real-time data)"""
        return self.get_scan_progress()
    
    def generate_scan_summary(self) -> Dict:
        """Generate comprehensive scan summary"""
        
        progress = self.get_scan_progress()
        top_aspects = self.get_top_affected_aspects()
        recent_actions = self.get_recent_actions()
        
        return {
            'scan_progress': progress,
            'top_affected_aspects': top_aspects,
            'recent_actions': recent_actions,
            'scan_timestamp': datetime.now().isoformat(),
            'next_scheduled_scan': (datetime.now() + timedelta(hours=6)).isoformat()
        }


# Singleton instance
diagnostics_service = DiagnosticsService()

