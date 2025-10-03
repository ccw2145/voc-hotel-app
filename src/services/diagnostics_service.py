"""
Diagnostics Service - Handles anomaly detection and real-time scanning operations
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid


class DiagnosticsService:
    """Service for anomaly detection and diagnostics operations"""
    
    def __init__(self):
        self._scan_results = {
            'newark-nj': {
                'property': 'Newark, NJ',
                'status': 'complete',
                'issues_found': False,
                'scan_time': '0:01',
                'reviews': 134,
                'avg_rating': 4.2,
                'top_theme': 'staff_friendliness',
                'completion_time': datetime.now() - timedelta(minutes=5)
            },
            'san-jose-ca': {
                'property': 'San Jose, CA',
                'status': 'complete',
                'issues_found': True,
                'scan_time': '0:02',
                'aspect': 'wifi_connectivity',
                'signal': '-22% vs 28d baseline',
                'signal_value': 5.02,
                'quick_action': 'Share Wi-Fi quick fixes',
                'completion_time': datetime.now() - timedelta(minutes=4)
            },
            'chicago-ohare': {
                'property': 'Chicago O\'Hare, IL',
                'status': 'issue_found',
                'issues_found': True,
                'scan_time': '0:02',
                'aspect': 'cleanliness',
                'signal': '-31% vs 28d baseline',
                'mentions': 29,
                'mentions_change': 2.9,
                'severity': 'critical',
                'completion_time': datetime.now() - timedelta(minutes=3)
            },
            'tampa-fl': {
                'property': 'Tampa, FL',
                'status': 'complete',
                'issues_found': False,
                'scan_time': '0:03',
                'completion_time': datetime.now() - timedelta(minutes=2)
            },
            'denver-downtown': {
                'property': 'Denver Downtown',
                'status': 'scanning',
                'issues_found': None,
                'scan_time': '0:03',
                'start_time': datetime.now() - timedelta(seconds=30)
            }
        }
    
    def kickoff_anomaly_workspace(self) -> Dict:
        """Initiate anomaly detection workspace"""
        
        workspace_id = f"ws_anomaly_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            'status': 'initiated',
            'workspace_id': workspace_id,
            'message': 'Anomaly detection workspace initiated successfully',
            'estimated_completion': (datetime.now() + timedelta(minutes=15)).isoformat(),
            'properties_to_scan': 120,
            'aspects_to_analyze': 20,
            'scan_type': 'comprehensive_anomaly_detection'
        }
    
    def get_scan_progress(self) -> Dict:
        """Get current scanning progress and statistics"""
        
        completed_scans = sum(1 for result in self._scan_results.values() 
                            if result['status'] in ['complete', 'issue_found'])
        
        total_anomalies = sum(1 for result in self._scan_results.values() 
                            if result.get('issues_found', False))
        
        critical_issues = sum(1 for result in self._scan_results.values() 
                            if result.get('severity') == 'critical')
        
        warning_issues = total_anomalies - critical_issues
        
        return {
            'properties_scanned': f"{completed_scans + 1} of 120",
            'anomalies_total': total_anomalies,
            'critical_count': critical_issues,
            'warning_count': warning_issues,
            'scan_status': 'in_progress',
            'completion_percentage': round((completed_scans / 120) * 100, 1)
        }
    
    def get_scan_results(self) -> List[Dict]:
        """Get detailed scan results for all properties"""
        
        results = []
        
        for prop_id, data in self._scan_results.items():
            result = {
                'property_id': prop_id,
                'property_name': data['property'],
                'status': data['status'],
                'scan_time': data['scan_time'],
                'issues_found': data.get('issues_found', False)
            }
            
            # Add additional details based on status
            if data['status'] == 'complete' and not data.get('issues_found', False):
                result.update({
                    'reviews': data.get('reviews'),
                    'avg_rating': data.get('avg_rating'),
                    'top_theme': data.get('top_theme')
                })
            
            elif data.get('issues_found', False):
                result.update({
                    'aspect': data.get('aspect'),
                    'signal': data.get('signal'),
                    'signal_value': data.get('signal_value'),
                    'mentions': data.get('mentions'),
                    'mentions_change': data.get('mentions_change'),
                    'severity': data.get('severity', 'warning'),
                    'quick_action': data.get('quick_action')
                })
            
            results.append(result)
        
        return results
    
    def get_top_affected_aspects(self) -> List[str]:
        """Get the most commonly affected aspects from current scan"""
        
        aspects = []
        for result in self._scan_results.values():
            if result.get('aspect'):
                aspects.append(result['aspect'])
        
        # Count occurrences and return top aspects
        aspect_counts = {}
        for aspect in aspects:
            aspect_counts[aspect] = aspect_counts.get(aspect, 0) + 1
        
        # Sort by count and return top 3
        sorted_aspects = sorted(aspect_counts.items(), key=lambda x: x[1], reverse=True)
        return [aspect for aspect, count in sorted_aspects[:3]]
    
    def get_recent_actions(self) -> Dict:
        """Get summary of recent actions taken"""
        
        # Mock recent actions data
        return {
            'emails_sent': 2,
            'tickets_opened': 1,
            'properties_flagged': 3,
            'last_action_time': datetime.now() - timedelta(minutes=15),
            'actions_today': 8
        }
    
    def simulate_scan_progress(self) -> Dict:
        """Simulate ongoing scan progress (for demo purposes)"""
        
        # Update Denver Downtown scan status
        if 'denver-downtown' in self._scan_results:
            current_time = datetime.now()
            start_time = self._scan_results['denver-downtown'].get('start_time', current_time)
            elapsed = (current_time - start_time).seconds
            
            if elapsed > 60:  # After 1 minute, complete the scan
                self._scan_results['denver-downtown'].update({
                    'status': 'complete',
                    'issues_found': False,
                    'completion_time': current_time,
                    'reviews': 187,
                    'avg_rating': 4.5,
                    'top_theme': 'excellent_location'
                })
        
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

