"""
Recommendations Service - Generates prescriptive recommendations for property improvements
"""

from typing import Dict, List, Optional
from .database_service import database_service
from functools import lru_cache
import time
import json


class RecommendationsService:
    """Service for generating prescriptive recommendations based on property issues"""
    
    def __init__(self):
        # Lakebase OLTP table (PostgreSQL schema.table format)
        self.runbook_schema = "voc"
        self.runbook_table = "aspect_runbook_db"
        self._cache_timestamp = None
        self._cache_duration = 300  # 5 minutes
    
    def _get_runbook_data(self) -> Dict[str, Dict]:
        """Get aspect runbook data from database with caching"""
        current_time = time.time()
        
        # Check if cache is still valid
        if self._cache_timestamp and (current_time - self._cache_timestamp) < self._cache_duration:
            if hasattr(self, '_runbook_cache'):
                return self._runbook_cache
        
        try:
            # Query Lakebase OLTP table using PostgreSQL syntax with service principal auth
            query = f"SELECT * FROM {self.runbook_schema}.{self.runbook_table}"
            
            # Use HQ credentials for runbook data (global configuration)
            result = database_service.query_lakebase(query, role='hq', property=None)
            
            if result is None:
                print("⚠️  Warning: Lakebase query returned None, using placeholder runbook data")
                return self._get_placeholder_runbook()
            
            # Convert to dictionary keyed by aspect
            runbook_dict = {}
            for row in result:
                aspect = row.get('aspect')
                if aspect:
                    # Parse action_items if it's a JSON string
                    action_items = row.get('action_items', '[]')
                    if isinstance(action_items, str):
                        try:
                            action_items = json.loads(action_items)
                        except json.JSONDecodeError:
                            # If not valid JSON, try splitting by newline or comma
                            action_items = [item.strip() for item in action_items.split('\n') if item.strip()]
                            if not action_items:
                                action_items = [item.strip() for item in action_items.split(',') if item.strip()]
                    
                    runbook_dict[aspect] = {
                        'action': row.get('action', ''),
                        'action_items': action_items if isinstance(action_items, list) else [],
                        'expected_impact': row.get('expected_impact', ''),
                        'timeline': row.get('timeline', ''),
                        'cost_estimate': row.get('cost_estimate', ''),
                        'difficulty': row.get('difficulty', '')
                    }
            
            self._runbook_cache = runbook_dict
            self._cache_timestamp = current_time
            print(f"✅ Loaded {len(runbook_dict)} runbook entries from database")
            return runbook_dict
            
        except Exception as e:
            print(f"⚠️  Warning: Error loading runbook data: {str(e)}")
            return self._get_placeholder_runbook()
    
    def _get_placeholder_runbook(self) -> Dict[str, Dict]:
        """Fallback placeholder runbook data"""
        return {
            'Room Cleanliness': {
                'action': 'Implement additional housekeeping quality checks and provide refresher training on deep cleaning protocols.',
                'action_items': [
                    'Schedule immediate housekeeping audit of all rooms',
                    'Review and replenish cleaning supply inventory',
                    'Implement guest room inspection checklist',
                    'Provide deep cleaning protocol training to housekeeping staff',
                    'Install quality control checkpoints in cleaning process'
                ],
                'expected_impact': 'Reduce negative cleanliness reviews by 60% within 2 weeks',
                'timeline': '2 weeks',
                'cost_estimate': 'Low-Medium',
                'difficulty': 'Medium'
            },
            'Staff Service': {
                'action': 'Enhance customer service training and implement guest interaction protocols.',
                'action_items': [
                    'Conduct comprehensive staff service training workshop',
                    'Implement standardized guest greeting procedures',
                    'Review and optimize response time protocols',
                    'Create guest service excellence guidelines',
                    'Establish regular service quality assessments'
                ],
                'expected_impact': 'Improve staff service ratings by 40% within 3 weeks',
                'timeline': '3 weeks',
                'cost_estimate': 'Low',
                'difficulty': 'Medium'
            },
            'WiFi Connectivity': {
                'action': 'Upgrade network infrastructure and implement redundant internet connections.',
                'action_items': [
                    'Upgrade to enterprise-grade WiFi equipment',
                    'Add backup internet service provider',
                    'Implement comprehensive network monitoring system',
                    'Conduct WiFi coverage analysis and optimization',
                    'Create guest network troubleshooting procedures'
                ],
                'expected_impact': 'Eliminate WiFi connectivity issues within 1 week',
                'timeline': '1 week',
                'cost_estimate': 'High',
                'difficulty': 'High'
            },
            'Noise Levels': {
                'action': 'Implement noise reduction measures and review room soundproofing.',
                'action_items': [
                    'Install additional soundproofing materials in affected rooms',
                    'Review and service HVAC systems for noise reduction',
                    'Implement and enforce quiet hours policy',
                    'Inspect and improve room-to-room sound isolation',
                    'Create noise complaint response procedures'
                ],
                'expected_impact': 'Reduce noise complaints by 50% within 4 weeks',
                'timeline': '4 weeks',
                'cost_estimate': 'Medium-High',
                'difficulty': 'High'
            },
            'Amenities': {
                'action': 'Audit and upgrade guest amenities based on feedback analysis.',
                'action_items': [
                    'Conduct comprehensive amenities audit',
                    'Review maintenance schedules for all facilities',
                    'Update amenity offerings based on guest preferences',
                    'Ensure consistent amenity availability and quality',
                    'Implement amenity feedback collection system'
                ],
                'expected_impact': 'Improve amenity satisfaction by 35% within 3 weeks',
                'timeline': '3 weeks',
                'cost_estimate': 'Medium',
                'difficulty': 'Medium'
            }
        }
    
    def generate_recommendations(self, property_data: Dict) -> List[Dict]:
        """Generate prescriptive recommendations for a property"""
        
        if not property_data or 'aspects' not in property_data:
            return []
        
        recommendations = []
        
        for aspect in property_data['aspects']:
            if aspect['status'] in ['critical', 'warning']:
                recommendation = self._create_recommendation(aspect, property_data)
                if recommendation:
                    recommendations.append(recommendation)
        
        return recommendations
    
    def _create_recommendation(self, aspect: Dict, property_data: Dict) -> Optional[Dict]:
        """Create a specific recommendation for an aspect"""
        
        aspect_name = aspect['name']
        status = aspect['status']
        percentage = aspect['percentage']
        
        # Get runbook data from database
        runbook_data = self._get_runbook_data()
        
        template = runbook_data.get(aspect_name)
        if not template:
            # Generic recommendation for unknown aspects
            template = {
                'action': f'Address {aspect_name.lower()} concerns through targeted improvement initiatives.',
                'action_items': [
                    f'Conduct detailed analysis of {aspect_name.lower()} issues',
                    'Develop targeted improvement plan',
                    'Implement corrective measures',
                    'Monitor progress and guest feedback',
                    'Adjust strategies based on results'
                ],
                'expected_impact': f'Improve {aspect_name.lower()} satisfaction within 2-4 weeks',
                'timeline': '2-4 weeks',
                'cost_estimate': 'Medium',
                'difficulty': 'Medium'
            }
        
        return {
            'aspect': aspect_name,
            'priority': status.title(),
            'severity_score': percentage,
            'action': template['action'],
            'action_items': template['action_items'],
            'expected_impact': template['expected_impact'],
            'timeline': template['timeline'],
            'cost_estimate': template['cost_estimate'],
            'difficulty': template['difficulty'],
            'property_name': property_data.get('name', 'Unknown Property')
        }
    
    def get_recommendation_summary(self, recommendations: List[Dict]) -> Dict:
        """Generate a summary of all recommendations"""
        
        if not recommendations:
            return {
                'total_recommendations': 0,
                'critical_count': 0,
                'warning_count': 0,
                'estimated_timeline': 'No actions required',
                'overall_priority': 'None'
            }
        
        critical_count = sum(1 for rec in recommendations if rec['priority'] == 'Critical')
        warning_count = sum(1 for rec in recommendations if rec['priority'] == 'Warning')
        
        # Determine overall priority
        if critical_count > 0:
            overall_priority = 'Critical'
        elif warning_count > 0:
            overall_priority = 'Warning'
        else:
            overall_priority = 'Low'
        
        # Estimate timeline based on most urgent items
        timelines = [rec['timeline'] for rec in recommendations]
        if any('1 week' in timeline for timeline in timelines):
            estimated_timeline = '1 week'
        elif any('2 weeks' in timeline for timeline in timelines):
            estimated_timeline = '2 weeks'
        else:
            estimated_timeline = '3-4 weeks'
        
        return {
            'total_recommendations': len(recommendations),
            'critical_count': critical_count,
            'warning_count': warning_count,
            'estimated_timeline': estimated_timeline,
            'overall_priority': overall_priority,
            'top_aspects': [rec['aspect'] for rec in recommendations[:3]]
        }


# Singleton instance
recommendations_service = RecommendationsService()
