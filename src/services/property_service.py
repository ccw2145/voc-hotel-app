"""
Property Service - Manages property data and health metrics for Lakehouse Inn properties
"""

from typing import Dict, List, Optional
from datetime import datetime


class PropertyService:
    """Service for managing property data and health metrics"""
    
    def __init__(self):
        self._property_data = {
            'denver-downtown': {
                'name': 'Denver Downtown',
                'city': 'Denver',
                'state': 'CO',
                'aspects': [
                    {'name': 'Room Cleanliness', 'percentage': 4.8, 'status': 'critical'},
                    {'name': 'Staff Service', 'percentage': 1.2, 'status': 'good'},
                    {'name': 'Amenities', 'percentage': 0.8, 'status': 'good'},
                    {'name': 'Location', 'percentage': 0.3, 'status': 'excellent'}
                ],
                'reviews_count': 234,
                'avg_rating': 4.2,
                'top_theme': 'room_cleanliness_issues'
            },
            'miami-beach': {
                'name': 'Miami Beach',
                'city': 'Miami',
                'state': 'FL',
                'aspects': [
                    {'name': 'Staff Service', 'percentage': 3.2, 'status': 'warning'},
                    {'name': 'Room Cleanliness', 'percentage': 1.1, 'status': 'good'},
                    {'name': 'Amenities', 'percentage': 2.1, 'status': 'good'},
                    {'name': 'Location', 'percentage': 0.2, 'status': 'excellent'}
                ],
                'reviews_count': 189,
                'avg_rating': 4.4,
                'top_theme': 'staff_service_concerns'
            },
            'chicago-loop': {
                'name': 'Chicago Loop',
                'city': 'Chicago',
                'state': 'IL',
                'aspects': [
                    {'name': 'Noise Levels', 'percentage': 3.1, 'status': 'warning'},
                    {'name': 'Room Cleanliness', 'percentage': 1.5, 'status': 'good'},
                    {'name': 'Staff Service', 'percentage': 0.9, 'status': 'good'},
                    {'name': 'Location', 'percentage': 0.4, 'status': 'excellent'}
                ],
                'reviews_count': 156,
                'avg_rating': 4.3,
                'top_theme': 'noise_complaints'
            },
            'austin-central': {
                'name': 'Austin Central',
                'city': 'Austin',
                'state': 'TX',
                'aspects': [
                    {'name': 'WiFi Connectivity', 'percentage': 5.1, 'status': 'critical'},
                    {'name': 'Room Cleanliness', 'percentage': 1.0, 'status': 'good'},
                    {'name': 'Staff Service', 'percentage': 1.3, 'status': 'good'},
                    {'name': 'Amenities', 'percentage': 2.0, 'status': 'good'}
                ],
                'reviews_count': 198,
                'avg_rating': 4.1,
                'top_theme': 'wifi_connectivity_issues'
            },
            'seattle-waterfront': {
                'name': 'Seattle Waterfront',
                'city': 'Seattle',
                'state': 'WA',
                'aspects': [
                    {'name': 'Room Cleanliness', 'percentage': 0.8, 'status': 'excellent'},
                    {'name': 'Staff Service', 'percentage': 0.6, 'status': 'excellent'},
                    {'name': 'Amenities', 'percentage': 1.1, 'status': 'good'},
                    {'name': 'Location', 'percentage': 0.2, 'status': 'excellent'}
                ],
                'reviews_count': 167,
                'avg_rating': 4.7,
                'top_theme': 'excellent_service'
            }
        }
    
    def get_all_properties(self) -> List[Dict]:
        """Get list of all properties"""
        return [
            {
                'id': prop_id,
                'name': data['name'],
                'city': data['city'],
                'state': data['state']
            }
            for prop_id, data in self._property_data.items()
        ]
    
    def get_property_details(self, property_id: str) -> Optional[Dict]:
        """Get detailed information for a specific property"""
        if property_id not in self._property_data:
            return None
            
        property_data = self._property_data[property_id]
        return {
            'property_id': property_id,
            'name': property_data['name'],
            'city': property_data['city'],
            'state': property_data['state'],
            'aspects': property_data['aspects'],
            'reviews_count': property_data['reviews_count'],
            'avg_rating': property_data['avg_rating'],
            'top_theme': property_data['top_theme']
        }
    
    def get_flagged_properties(self) -> List[Dict]:
        """Get properties with critical or warning issues"""
        flagged = []
        
        for prop_id, data in self._property_data.items():
            for aspect in data['aspects']:
                if aspect['status'] in ['critical', 'warning']:
                    flagged.append({
                        'property': data['name'],
                        'property_id': prop_id,
                        'aspect': aspect['name'],
                        'negative_percentage': aspect['percentage'],
                        'status': aspect['status']
                    })
        
        return flagged
    
    def get_diagnostics_kpis(self) -> Dict:
        """Calculate overall diagnostics KPIs across all properties"""
        total_reviews = sum(data['reviews_count'] for data in self._property_data.values())
        avg_rating = sum(data['avg_rating'] for data in self._property_data.values()) / len(self._property_data)
        
        # Calculate negative review percentage
        total_negative = 0
        total_aspects = 0
        
        for data in self._property_data.values():
            for aspect in data['aspects']:
                total_negative += aspect['percentage']
                total_aspects += 1
        
        avg_negative = total_negative / total_aspects if total_aspects > 0 else 0
        
        # Count flagged properties
        flagged_count = len(set(
            prop_id for prop_id, data in self._property_data.items()
            if any(aspect['status'] in ['critical', 'warning'] for aspect in data['aspects'])
        ))
        
        return {
            'avg_negative_reviews_7d': round(avg_negative, 1),
            'properties_flagged': flagged_count,
            'overall_satisfaction': round((100 - avg_negative), 1),
            'reviews_processed_today': total_reviews,
            'trends': {
                'negative_reviews_change': -0.5,
                'flagged_properties_change': 2,
                'satisfaction_change': 1.2
            }
        }


# Singleton instance
property_service = PropertyService()

