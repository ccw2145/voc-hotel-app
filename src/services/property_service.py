"""
Property Service - Manages property data and health metrics for Lakehouse Inn properties
"""

from typing import Dict, List, Optional
from datetime import datetime
import json
from .database_service import database_service


class PropertyService:
    """Service for managing property data and health metrics"""
    
    def __init__(self):
        self.issues_table = "lakehouse_inn_catalog.voc.open_issues_diagnosis"
        self.reviews_table = "lakehouse_inn_catalog.voc.review_aspect_details"
        self.hotels_table = "lakehouse_inn_catalog.voc.hotel_locations"
        self._cache = {}
        self._cache_timestamp = None
        self._hotels_cache = None
        self._hotels_cache_timestamp = None
        # Auth context for service principal authentication
        self._role = 'hq'
        self._property = None
    
    def set_auth_context(self, role: str = 'hq', property: str = None):
        """Set authentication context for service principal selection"""
        self._role = role
        self._property = property
    
    def _get_placeholder_data(self) -> List[Dict]:
        """Return placeholder data when database is unavailable"""
        return [
            {
                'location': 'Denver, CO', 'aspect': 'cleanliness', 'severity': 'Critical', 'status': 'Open', 
                'open_reason': 'cleanliness_complaints', 'nms_open': 0.48, 'opened_at': '2024-01-15',
                'response_data': {"aspect": "cleanliness", "issue_summary": "Multiple guests reported unclean rooms with dust, hair, and bathroom issues. 15 negative reviews in the past 7 days.", "potential_root_cause": "Understaffing during peak season and inadequate quality control checks.", "impact": "48% of reviews mention cleanliness issues, affecting overall rating and guest satisfaction.", "recommended_action": "Implement daily housekeeping quality audits and hire 2 additional staff members."}
            },
            {
                'location': 'Denver, CO', 'aspect': 'Staff Service', 'severity': 'Good', 'status': 'Open', 
                'open_reason': 'service_feedback', 'nms_open': 0.012, 'opened_at': '2024-01-15',
                'response_data': {"aspect": "Staff Service", "issue_summary": "Generally positive feedback with occasional slow response times.", "potential_root_cause": "Peak hour coverage gaps.", "impact": "1.2% negative mentions, minimal impact on ratings.", "recommended_action": "Adjust staff scheduling for peak hours."}
            },
            {
                'location': 'Miami, FL', 'aspect': 'Staff Service', 'severity': 'Warning', 'status': 'Open', 
                'open_reason': 'service_delays', 'nms_open': 0.032, 'opened_at': '2024-01-14',
                'response_data': {"aspect": "Staff Service", "issue_summary": "Guests experiencing delays at check-in and slow response to requests. 12 complaints in past week.", "potential_root_cause": "Insufficient front desk coverage during high occupancy periods.", "impact": "3.2% of reviews cite service delays, impacting guest experience scores.", "recommended_action": "Add front desk staff during peak hours and implement request tracking system."}
            },
            {
                'location': 'Miami, FL', 'aspect': 'Amenities', 'severity': 'Good', 'status': 'Open', 
                'open_reason': 'amenity_concerns', 'nms_open': 0.021, 'opened_at': '2024-01-14',
                'response_data': {"aspect": "Amenities", "issue_summary": "Pool and gym equipment mentioned in 8 reviews as needing maintenance.", "potential_root_cause": "Delayed maintenance schedule.", "impact": "2.1% negative mentions about amenities.", "recommended_action": "Schedule immediate equipment inspection and repairs."}
            },
            {
                'location': 'Chicago, IL', 'aspect': 'noise_ambience', 'severity': 'Warning', 'status': 'Open', 
                'open_reason': 'noise_complaints', 'nms_open': 0.031, 'opened_at': '2024-01-13',
                'response_data': {"aspect": "noise_ambience", "issue_summary": "Guests consistently report noise disturbances from the nearby street, with multiple reviews citing this specific issue across different dates and booking channels.", "potential_root_cause": "The hotel's proximity to a busy street generates ongoing noise pollution that penetrates guest rooms. Inadequate soundproofing or window insulation may be allowing street noise to disrupt the indoor environment.", "impact": "Street noise negatively affects guest comfort and sleep quality, leading to reduced satisfaction as evidenced by moderate star ratings.", "recommended_action": "Install or upgrade soundproofing materials, particularly around windows facing the street. Consider offering rooms on higher floors or away from street-facing sides to noise-sensitive guests."}
            },
            {
                'location': 'Chicago, IL', 'aspect': 'Room Cleanliness', 'severity': 'Good', 'status': 'Open', 
                'open_reason': 'cleanliness_feedback', 'nms_open': 0.015, 'opened_at': '2024-01-13',
                'response_data': {"aspect": "Room Cleanliness", "issue_summary": "Generally clean with minor issues in 5 reviews.", "potential_root_cause": "Minor oversights in quality checks.", "impact": "1.5% mention cleanliness, mostly positive.", "recommended_action": "Continue current practices with spot checks."}
            },
            {
                'location': 'Austin, TX', 'aspect': 'WiFi Connectivity', 'severity': 'Critical', 'status': 'Open', 
                'open_reason': 'connectivity_issues', 'nms_open': 0.051, 'opened_at': '2024-01-12',
                'response_data': {"aspect": "WiFi Connectivity", "issue_summary": "Frequent disconnections and slow speeds reported by 18 guests. Business travelers particularly affected.", "potential_root_cause": "Outdated router equipment and insufficient bandwidth for current occupancy.", "impact": "5.1% of reviews cite WiFi issues, highest complaint category affecting business traveler satisfaction.", "recommended_action": "Immediate router upgrade and bandwidth increase. Consider backup internet provider."}
            },
            {
                'location': 'Austin, TX', 'aspect': 'Amenities', 'severity': 'Good', 'status': 'Open', 
                'open_reason': 'amenity_requests', 'nms_open': 0.020, 'opened_at': '2024-01-12',
                'response_data': {"aspect": "Amenities", "issue_summary": "Requests for upgraded fitness equipment in 7 reviews.", "potential_root_cause": "Aging gym equipment.", "impact": "2.0% mention amenities, mostly suggestions.", "recommended_action": "Budget for gym equipment refresh in Q2."}
            },
            {
                'location': 'Seattle, WA', 'aspect': 'Room Cleanliness', 'severity': 'Excellent', 'status': 'Open', 
                'open_reason': 'minor_feedback', 'nms_open': 0.008, 'opened_at': '2024-01-11',
                'response_data': {"aspect": "Room Cleanliness", "issue_summary": "Excellent cleanliness with only 2 minor mentions, both positive.", "potential_root_cause": "N/A - performing well.", "impact": "0.8% mention cleanliness, all positive feedback.", "recommended_action": "Maintain current standards and recognize housekeeping team."}
            },
            {
                'location': 'Seattle, WA', 'aspect': 'Amenities', 'severity': 'Good', 'status': 'Open', 
                'open_reason': 'amenity_feedback', 'nms_open': 0.011, 'opened_at': '2024-01-11',
                'response_data': {"aspect": "Amenities", "issue_summary": "Generally satisfied, 3 reviews mention amenities positively.", "potential_root_cause": "N/A - performing well.", "impact": "1.1% mention amenities, mostly positive.", "recommended_action": "Continue current amenity offerings."}
            },
        ]
    def _get_reviews_data(self) -> List[Dict]:
        """Fetch reviews data from Databricks table with caching"""
        if (self._reviews_cache_timestamp and 
            (datetime.now() - self._reviews_cache_timestamp).seconds < 600):
            return self._reviews_cache or []
        
        try:
            query = f"""
                SELECT 
                    review_uid, 
                    review_date,
                    location
                FROM {self.reviews_table}
                GROUP BY review_uid,location, review_date
            """
            reviews = database_service.query(query, role=self._role, property=self._property)
            reviews_list = []
            for review in reviews:
                hotels_list.append({
                    'location': hotel.get('location'),
                    'latitude': float(hotel.get('latitude', 0)),
                    'longitude': float(hotel.get('longitude', 0))
                })
            
            # Update cache
            self._hotels_cache = hotels_list
            self._hotels_cache_timestamp = datetime.now()
            
            print(f"✅ Fetched {len(hotels_list)} hotel locations from {self.hotels_table}")
            return hotels_list
            self._reviews_cache = reviews
            self._cache_timestamp = datetime.now()
            return reviews
        except Exception as e:
            print(f"⚠️  Error fetching reviews data: {str(e)}")
            return []

    def _get_hotel_locations(self) -> List[Dict]:
        """Fetch all hotel locations from Databricks table with caching"""
        # Cache for 10 minutes (hotel locations don't change often)
        if (self._hotels_cache_timestamp and 
            (datetime.now() - self._hotels_cache_timestamp).seconds < 600):
            return self._hotels_cache or []
        
        try:
            query = f"""
                SELECT 
                    location,
                    latitude,
                    longitude
                FROM {self.hotels_table}
            """
            
            hotels = database_service.query(query, role=self._role, property=self._property)
            
            if hotels is None:
                print("📊 Using placeholder hotel locations")
                return self._get_placeholder_hotel_locations()
            
            # Convert to list of dicts
            hotels_list = []
            for hotel in hotels:
                hotels_list.append({
                    'location': hotel.get('location'),
                    'latitude': float(hotel.get('latitude', 0)),
                    'longitude': float(hotel.get('longitude', 0))
                })
            
            # Update cache
            self._hotels_cache = hotels_list
            self._hotels_cache_timestamp = datetime.now()
            
            print(f"✅ Fetched {len(hotels_list)} hotel locations from {self.hotels_table}")
            return hotels_list
            
        except Exception as e:
            print(f"⚠️  Error fetching hotel locations: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._get_placeholder_hotel_locations()
    
    def _get_placeholder_hotel_locations(self) -> List[Dict]:
        """Placeholder hotel locations when database is unavailable"""
        return [
            {'location': 'Denver, CO', 'latitude': 39.7392, 'longitude': -104.9903},
            {'location': 'Miami, FL', 'latitude': 25.7617, 'longitude': -80.1918},
            {'location': 'Chicago, IL', 'latitude': 41.8781, 'longitude': -87.6298},
            {'location': 'Austin, TX', 'latitude': 30.2672, 'longitude': -97.7431},
            {'location': 'Seattle, WA', 'latitude': 47.6062, 'longitude': -122.3321},
        ]
    
    def _get_issues_data(self, days: Optional[int] = None) -> List[Dict]:
        """Fetch issues data from Databricks table with caching
        
        Args:
            days: Number of days to look back from current date. If None, get all open issues.
        """
        # Only use cache if no days filter (all data)
        if days is None and self._cache_timestamp and (datetime.now() - self._cache_timestamp).seconds < 300:
            return self._cache.get('issues', [])
        
        try:
            # Build date filter based on days parameter (using latest opened_at as reference)
            if days is not None:
                date_filter = f"AND opened_at >= latest_opened_at - INTERVAL {days} DAYS"
            else:
                date_filter = ""
            
            query = f"""
                WITH latest_date_cte AS (
                    SELECT 
                        MAX(opened_at) AS latest_opened_at
                    FROM {self.issues_table}
                    WHERE status = 'Open'
                )
                SELECT 
                    location,
                    aspect,
                    severity,
                    status,
                    open_reason,
                    nms_open,
                    volume_open,
                    opened_at,
                    from_json(
                        response_result,
                        'STRUCT<
                            aspect: STRING,
                            issue_summary: STRING,
                            potential_root_cause: STRING,
                            impact: STRING,
                            recommended_action: STRING
                        >'
                    ) as response_data
                FROM {self.issues_table}
                CROSS JOIN latest_date_cte
                WHERE status = 'Open'
                {date_filter}
            """
            
            issues = database_service.query(query, role=self._role, property=self._property)
            
            # Use placeholder data if query returns None (connection failed)
            if issues is None:
                print("📊 Using placeholder data for property service")
                return self._get_placeholder_data()
            
            # Convert to list of dicts if needed
            if hasattr(issues, 'fetchall'):
                rows = issues.fetchall()
                columns = [desc[0] for desc in issues.description]
                issues = [dict(zip(columns, row)) for row in rows]
            
            # Cache the results
            self._cache['issues'] = issues
            self._cache_timestamp = datetime.now()
            
            return issues
            
        except Exception as e:
            print(f"⚠️ Error querying issues data: {e}")
            print("📊 Falling back to placeholder data")
            return self._get_placeholder_data()
    
    def _parse_location(self, location: str) -> Dict[str, str]:
        """Parse location string into city and state"""
        if ',' in location:
            parts = location.split(',')
        else:
            parts = [location]
        
        return {
            'city': parts[0].strip(),
            'state': parts[1].strip() if len(parts) > 1 else ''
        }
    
    
    def get_all_properties(self) -> List[Dict]:
        """Get list of all properties from hotel_locations table, merged with issues data"""
        # Get all hotel locations (source of truth for all 120 properties)
        hotels = self._get_hotel_locations()
        issues = self._get_issues_data()
        # has_reviews = self._get_reviews_data()
        # Group issues by location
        issues_map = {}
        for issue in issues:
            location = issue.get('location', 'Unknown')
            if location not in issues_map:
                issues_map[location] = []
            issues_map[location].append(issue)
        
        # Convert to property list
        properties = []
        for hotel in hotels:
            location = hotel['location']
            parsed = self._parse_location(location)
            property_id = location.lower().replace(' ', '-').replace(',', '')
            
            # Get issues for this property (if any)
            property_issues = issues_map.get(location, [])
            
            if property_issues:
                # Property has issues - process them
                # Aggregate aspects from issues
                aspects_map = {}
                for issue in property_issues:
                    aspect = issue.get('aspect', 'Unknown')
                    nms_open = float(issue.get('nms_open', 0))
                    # Read severity directly from issues table
                    severity = issue.get('severity', 'Unknown').lower()
                    
                    if aspect not in aspects_map or nms_open > aspects_map[aspect]['percentage']:
                        aspects_map[aspect] = {
                            'name': aspect,
                            'percentage': nms_open,
                            'status': severity
                        }
                
                aspects = list(aspects_map.values())
                
                # # Calculate aggregate metrics
                # total_volume = sum(a['percentage'] for a in aspects)
                # avg_volume = total_volume / len(aspects) if aspects else 0
                
                # Estimate rating based on volume (inverse relationship)
                # estimated_rating = max(1.0, min(5.0, 5.0 - (avg_volume / 2)))
                
                # Get top issue theme
                top_issue = max(property_issues, key=lambda x: float(x.get('nms_open', 0)))
                top_theme = top_issue.get('open_reason', 'no_issues')
            else:
                # Property has no issues - mark as healthy
                aspects = []
                # avg_volume = 0
                # estimated_rating = 5.0
                top_theme = 'no_issues'
          
            properties.append({
                'property_id': property_id,
                'name': location,
                'city': parsed['city'],
                'state': parsed['state'],
                'latitude': hotel.get('latitude', 0),
                'longitude': hotel.get('longitude', 0),
                'aspects': aspects,
                'reviews_count': len(property_issues),
                # 'avg_rating': round(estimated_rating, 1),
                'top_theme': top_theme,
                'has_issues': len(property_issues) > 0
            })
        
        return properties
    
    def get_property_details(self, property_id: str) -> Optional[Dict]:
        """Get detailed information for a specific property"""
        issues = self._get_issues_data()
        
        # Filter issues for this property
        property_issues = [
            issue for issue in issues 
            if issue.get('location', '').lower().replace(' ', '-').replace(',', '') == property_id
        ]
        
        if not property_issues:
            return None
        
        # Get location from first issue
        location = property_issues[0].get('location', 'Unknown')
        parsed = self._parse_location(location)
        
        # Aggregate aspects from issues
        aspects_map = {}
        for issue in property_issues:
            aspect = issue.get('aspect', 'Unknown')
            nms_open = float(issue.get('nms_open', 0))
            # Read severity directly from issues table
            severity = issue.get('severity', 'Unknown').lower()
            
            if aspect not in aspects_map or nms_open > aspects_map[aspect]['percentage']:
                aspects_map[aspect] = {
                    'name': aspect,
                    'percentage': nms_open,  # nms_open is already a percentage (5.1 = 5.1%)
                    'status': severity
                }
        
        aspects = list(aspects_map.values())
        
        # Get actual review count and rating from reviews table
        reviews_count, avg_rating = self._get_property_review_stats(location)
        
        # Get top issue theme
        top_issue = max(property_issues, key=lambda x: float(x.get('nms_open', 0))) if property_issues else {}
        top_theme = top_issue.get('open_reason', 'no_issues')
        
        return {
            'property_id': property_id,
            'name': location,
            'city': parsed['city'],
            'state': parsed['state'],
            'aspects': aspects,
            'reviews_count': reviews_count,
            'avg_rating': avg_rating,
            'top_theme': top_theme,
            'issues': property_issues
        }
    
    def _get_property_review_stats(self, location: str) -> tuple:
        """Get actual review count and average rating for a property from reviews table"""
        try:
            query = f"""
            SELECT 
                COUNT(DISTINCT review_uid) AS review_count,
                AVG(avg_rating) AS avg_rating
                FROM (
                SELECT 
                    review_uid, 
                    star_rating, 
                    AVG(star_rating) AS avg_rating
                FROM {self.reviews_table}
                WHERE location = '{location}'
                GROUP BY review_uid, star_rating
                ) t;
            """
            #             SELECT 
            #     COUNT(DISTINCT review_uid) AS review_count,
            #     AVG(star_rating) AS avg_rating
            # FROM {self.reviews_table}
            # WHERE location = '{location}'

            rows = database_service.query(query, role=self._role, property=self._property)
            
            if rows and len(rows) > 0:
                row = rows[0]
                review_count = int(row.get('review_count', 0))
                avg_rating = float(row.get('avg_rating', 0.0)) if row.get('avg_rating') else 0.0
                return review_count, round(avg_rating, 1)
            else:
                return 0, 0.0
        except Exception as e:
            print(f"⚠️  Error fetching review stats for {location}: {str(e)}")
            # Fallback to placeholder
            return 0, 0.0
    
    def get_flagged_properties(self) -> List[Dict]:
        """Get properties with critical or warning issues from database"""
        issues = self._get_issues_data()
        flagged = []
        for issue in issues:
            nms_open = float(issue.get('nms_open', 0))
            # Read severity directly from issues table
            severity = issue.get('severity', 'Unknown').lower()
            if severity in ['critical', 'warning']:
                location = issue.get('location', 'Unknown')
                prop_id = location.lower().replace(' ', '-').replace(',', '')
                flagged.append({
                    'property': location,
                    'property_id': prop_id,
                    'aspect': issue.get('aspect', 'Unknown'),
                    'negative_percentage': nms_open,  # nms_open is already a percentage
                    'status': severity
                })
        return flagged
    
    def get_flagged_properties_grouped(self) -> List[Dict]:
        """Get properties grouped by property_id with all their issues"""
        issues = self._get_issues_data()
        
        # Group by property
        properties = {}
        for issue in issues:
            nms_open = float(issue.get('nms_open', 0))
            # Read severity directly from issues table
            severity = issue.get('severity', 'Unknown').lower()
            
            if severity in ['critical', 'warning']:
                location = issue.get('location', 'Unknown')
                prop_id = location.lower().replace(' ', '-').replace(',', '')
                
                if prop_id not in properties:
                    properties[prop_id] = {
                        'property': location,
                        'property_id': prop_id,
                        'aspects': [],
                        'severity': 'warning'  # Start with warning
                    }
                
                # Add aspect details
                properties[prop_id]['aspects'].append({
                    'aspect': issue.get('aspect', 'Unknown'),
                    'negative_percentage': nms_open,  # nms_open is already a percentage
                    'status': severity
                })
                
                # Upgrade to critical if any issue is critical
                if severity == 'critical':
                    properties[prop_id]['severity'] = 'critical'
        
        return list(properties.values())
    
    def get_aspects_coverage(self, days: Optional[int] = None) -> Dict:
        """Get aspects coverage: how many aspects have issues vs total possible aspects
        
        Args:
            days: Number of days to look back. If None, use all issues.
        """
        # Get unique aspects from issues data (filtered by timeframe)
        issues = self._get_issues_data(days=days)
        aspects_with_issues = set()
        for issue in issues:
            aspect = issue.get('aspect')
            if aspect:
                aspects_with_issues.add(aspect)
        
        # Get total possible aspects from runbook
        from services.recommendations_service import recommendations_service
        runbook_data = recommendations_service._get_runbook_data()
  
        # Handle both dict and string formats
        unique_aspects = set(runbook_data.keys())
        # for item in runbook_data:
        #     if isinstance(item, dict):
        #         aspect = item.get('aspect')
        #         if aspect:
        #             unique_aspects.add(aspect)
        #     elif isinstance(item, str):
        #         # If item is already a string aspect name
        #         unique_aspects.add(item)
        
        total_possible_aspects = len(unique_aspects)
        
        return {
            'aspects_with_issues': len(aspects_with_issues),
            'total_aspects': total_possible_aspects
        }
    
    def get_healthy_properties_grouped(self) -> Dict:
        """Get healthy properties grouped by 'healthy' vs 'no_reviews'"""
        all_properties = self.get_all_properties()
        
        # Get flagged property IDs from the issues table
        issues = self._get_issues_data()
        flagged_locations = set()
        for issue in issues:
            # Read severity directly from issues table
            severity = issue.get('severity', 'Unknown').lower()
            if severity in ['critical', 'warning']:
                location = issue.get('location', 'Unknown')
                flagged_locations.add(location)
        
        grouped = {
            'healthy': [],  # Has reviews, no issues
            'no_reviews': []  # No recent review data
        }
        
        for prop in all_properties:
            # Skip flagged properties
            location = f"{prop['city']}, {prop['state']}"
            top_theme = prop['top_theme']
            reviews_count = prop['reviews_count']
            # if location in flagged_locations:
            #     continue
            
            # Check if property has any review data in issues table
            has_review_data = reviews_count > 0
            
            if has_review_data:
                # Has reviews but no critical/warning issues
                grouped['healthy'].append(prop)
            else:
                # No review data at all
                grouped['no_reviews'].append(prop)
        
        return grouped
    
    def get_diagnostics_kpis(self, days: Optional[int] = 21) -> Dict:
        """Calculate overall diagnostics KPIs using review_aspect_details table
        
        Args:
            days: Number of days to look back from latest review. If None, use all historical data.
        """
        # Get total properties count from hotel_locations table (source of truth)
        hotels = self._get_hotel_locations()
        total_properties = len(hotels)
        
        # Try to get stats from reviews table first
        review_stats = self.get_summary_stats_from_reviews(days=days)
        
        if review_stats['total_reviews'] > 0:
            # Use review stats
            overall_satisfaction = 100 - review_stats['avg_negative_reviews']
            
            # Get flagged properties from issues table (filtered by same timeframe)
            issues = self._get_issues_data(days=days)
            flagged_properties = set()
            for issue in issues:
                # Read severity directly from issues table
                severity = issue.get('severity', 'Unknown').lower()
                if severity in ['critical', 'warning']:
                    flagged_properties.add(issue.get('location', 'Unknown'))
            
            # Get aspects coverage (also filtered by timeframe)
            aspects_coverage = self.get_aspects_coverage(days=days)
            
            return {
                'avg_negative_reviews': review_stats['avg_negative_reviews'],
                'properties_flagged': len(flagged_properties),
                'total_properties': total_properties,
                'overall_satisfaction': round(overall_satisfaction, 1),
                'reviews_processed': review_stats['reviews_processed'],
                'aspects_with_issues': aspects_coverage['aspects_with_issues'],
                'total_aspects': aspects_coverage['total_aspects'],
                'trends': {
                    'negative_reviews_change': 0,
                    'flagged_properties_change': 0,
                    'satisfaction_change': 0.0
                }
            }
        
        # Fallback to issues table (filtered by same timeframe)
        issues = self._get_issues_data(days=days)
        
        # Get aspects coverage (filtered by timeframe)
        aspects_coverage = self.get_aspects_coverage(days=days)
        
        if not issues:
            return {
                'avg_negative_reviews': 0,
                'properties_flagged': 0,
                'total_properties': total_properties,
                'overall_satisfaction': 85.0,
                'reviews_processed': 0,
                'aspects_with_issues': aspects_coverage['aspects_with_issues'],
                'total_aspects': aspects_coverage['total_aspects'],
                'trends': {
                    'negative_reviews_change': 0,
                    'flagged_properties_change': 0,
                    'satisfaction_change': 0.0
                }
            }
        
        total_nms = sum(float(issue.get('nms_open', 0)) for issue in issues)
        avg_negative = total_nms / len(issues) if issues else 0
        
        flagged_properties = set()
        for issue in issues:
            # Read severity directly from issues table
            severity = issue.get('severity', 'Unknown').lower()
            if severity in ['critical', 'warning']:
                flagged_properties.add(issue.get('location', 'Unknown'))
        
        overall_satisfaction = max(0, min(100, 100 - avg_negative))
        
        return {
            'avg_negative_reviews': round(avg_negative, 1),
            'properties_flagged': len(flagged_properties),
            'total_properties': total_properties,
            'overall_satisfaction': round(overall_satisfaction, 1),
            'reviews_processed': len(issues),
            'aspects_with_issues': aspects_coverage['aspects_with_issues'],
            'total_aspects': aspects_coverage['total_aspects'],
            'trends': {
                'negative_reviews_change': 0,
                'flagged_properties_change': 0,
                'satisfaction_change': 0.0
            }
        }
    
    def get_reviews_deep_dive(self, property_id: str, aspect: Optional[str] = None) -> Dict:
        """Get detailed reviews deep dive for a property and specific aspect"""
        issues = self._get_issues_data()
        
        # Filter issues for this property
        property_issues = [
            issue for issue in issues 
            if issue.get('location', '').lower().replace(' ', '-').replace(',', '') == property_id
        ]
        
        if not property_issues:
            return {
                'aspects': [],
                'selected_aspect': None,
                'deep_dive': None
            }
        
        # Get unique aspects for this property
        aspects = list(set(issue.get('aspect', 'Unknown') for issue in property_issues))
        
        # If no aspect selected, return just the aspects list
        if not aspect:
            return {
                'aspects': sorted(aspects),
                'selected_aspect': None,
                'deep_dive': None
            }
        
        # Filter for selected aspect
        aspect_issues = [issue for issue in property_issues if issue.get('aspect') == aspect]
        
        if not aspect_issues:
            return {
                'aspects': sorted(aspects),
                'selected_aspect': aspect,
                'deep_dive': None
            }
        
        # Get the primary issue (highest nms_open)
        primary_issue = max(aspect_issues, key=lambda x: float(x.get('nms_open', 0)))
        
        # Extract response_data (already parsed by from_json in SQL)
        response_data = {}
        response_data_obj = primary_issue.get('response_data')
        if response_data_obj:
            if isinstance(response_data_obj, dict):
                response_data = response_data_obj
            elif hasattr(response_data_obj, '__dict__'):
                # Handle Row object from databricks-sql-connector
                response_data = {k: getattr(response_data_obj, k, None) for k in ['aspect', 'issue_summary', 'potential_root_cause', 'impact', 'recommended_action']}
        
        # Calculate review counts based on nms_open and volume_open
        nms_open_value = float(primary_issue.get('nms_open', 0))  # Decimal (e.g., 0.409 = 40.9%)
        volume_open = int(primary_issue.get('volume_open', 0))  # Total number of reviews
        
        # Convert to percentage for display
        nms_percentage = nms_open_value * 100
        
        # Calculate actual counts
        # negative_count = nms_open * volume_open
        negative_count = int(nms_open_value * volume_open)
        # Total reviews = volume_open
        total_reviews = volume_open
        positive_count = total_reviews - negative_count
        
        # Get open_reason
        open_reason = primary_issue.get('open_reason', 'Not specified')
        return {
            'aspects': sorted(aspects),
            'selected_aspect': aspect,
            'deep_dive': {
                'aspect': response_data.get('aspect', aspect),
                'issue_summary': response_data.get('issue_summary', 'No detailed summary available.'),
                'potential_root_cause': response_data.get('potential_root_cause', 'Under investigation.'),
                'impact': response_data.get('impact', f'{nms_percentage:.1f}% of reviews mention this aspect negatively.'),
                'recommended_action': response_data.get('recommended_action', 'Further analysis required.'),
                'negative_count': negative_count,
                'positive_count': positive_count,
                'total_reviews': total_reviews,
                'volume_percentage': int(round(nms_percentage)),
                'severity': primary_issue.get('severity', 'Unknown'),
                'date_opened': primary_issue.get('opened_at', 'Unknown'),
                'open_reason': open_reason
            }
        }
    
    def get_reviews_for_aspect(self, property_id: str, aspect: str, days_back: int = 30, limit: int = 50) -> List[Dict]:
        """Get individual reviews for a specific property and aspect"""
        try:
            # Get property location and issue opened_at date
            issues = self._get_issues_data()
            property_issues = [
                issue for issue in issues 
                if issue.get('location', '').lower().replace(' ', '-').replace(',', '') == property_id
            ]
            
            # Check if property_issues is empty
            if len(property_issues) == 0:
                return []
            
            location = property_issues[0].get('location', '')
            
            # Find the issue for this specific aspect to get opened_at date
            aspect_issue = next(
                (issue for issue in property_issues if issue.get('aspect') == aspect),
                property_issues[0]  # Fallback to first issue if aspect not found
            )
            # print(aspect_issue)
            opened_at = aspect_issue.get('opened_at', None)
            
            # Build date filter - use opened_at if available, otherwise use CURRENT_DATE
            if opened_at:
                date_filter = f"review_date >= DATE('{opened_at}') - INTERVAL {days_back} DAYS AND review_date <= DATE('{opened_at}')"
            else:
                date_filter = f"review_date >= CURRENT_DATE - INTERVAL {days_back} DAYS"
            # print("$$$$$$$$$$$$$",date_filter)
            # Query ALL reviews from review_aspect_details table (both positive and negative)
            query = f"""
                SELECT 
                    review_uid,
                    aspect,
                    sentiment,
                    evidence,
                    opinion_terms,
                    star_rating,
                    review_date,
                    review_text,
                    channel
                FROM {self.reviews_table}
                WHERE location = '{location}'
                  AND aspect = '{aspect}'
                  AND {date_filter}
                ORDER BY 
                    CASE 
                        WHEN sentiment IN ('negative', 'very_negative') THEN 0
                        ELSE 1
                    END,
                    review_date DESC
                LIMIT {limit}
            """

            rows = database_service.query(query, role=self._role, property=self._property)
            # print(rows)
            # Check if rows is empty (handle arrays properly)
            if rows is None or len(rows) == 0:
                return {'positive': [], 'negative': []}
            
            positive_reviews = []
            negative_reviews = []
            for row in rows:
                # Extract evidence and opinion terms (they are arrays)
                # Database returns rows as dictionaries
                evidence = row.get('evidence', [])
                opinion_terms = row.get('opinion_terms', [])
                sentiment = row.get('sentiment', '')
                
                # Convert to list if needed (handle numpy arrays, tuples, etc.)
                if evidence is not None and not isinstance(evidence, list):
                    if hasattr(evidence, 'tolist'):  # numpy array
                        evidence = evidence.tolist()
                    elif isinstance(evidence, (tuple, set)):
                        evidence = list(evidence)
                    else:
                        evidence = [str(evidence)]
                elif evidence is None:
                    evidence = []
                    
                if opinion_terms is not None and not isinstance(opinion_terms, list):
                    if hasattr(opinion_terms, 'tolist'):  # numpy array
                        opinion_terms = opinion_terms.tolist()
                    elif isinstance(opinion_terms, (tuple, set)):
                        opinion_terms = list(opinion_terms)
                    else:
                        opinion_terms = [str(opinion_terms)]
                elif opinion_terms is None:
                    opinion_terms = []
                
                review_data = {
                    'review_uid': row.get('review_uid'),
                    'aspect': row.get('aspect'),
                    'sentiment': sentiment,
                    'evidence': evidence,
                    'opinion_terms': opinion_terms,
                    'star_rating': row.get('star_rating'),
                    'review_date': str(row.get('review_date', 'N/A')),
                    'review_text': row.get('review_text'),
                    'channel': row.get('channel')
                }
                
                # Categorize by sentiment
                if sentiment in ('negative', 'very_negative'):
                    negative_reviews.append(review_data)
                else:
                    positive_reviews.append(review_data)
            
            return {
                'positive': positive_reviews,
                'negative': negative_reviews
            }
            
        except Exception as e:
            print(f"⚠️  Error fetching reviews: {str(e)}")
            import traceback
            traceback.print_exc()
            # Return placeholder data
            return self._get_placeholder_reviews(aspect)
    
    def _get_placeholder_reviews(self, aspect: str) -> Dict:
        """Placeholder reviews for when database is unavailable - returns dict with positive and negative reviews"""
        return {
            'negative': [
                {
                    'review_uid': 'review_001',
                    'aspect': aspect,
                    'sentiment': 'negative',
                    'evidence': ['The room was not clean', 'found dust on furniture'],
                    'opinion_terms': ['dirty', 'unclean'],
                    'star_rating': 2,
                    'review_date': '2024-10-15',
                    'review_text': 'The room was not clean. I found dust on the furniture and the bathroom needed attention.',
                    'channel': 'Google'
                },
                {
                    'review_uid': 'review_002',
                    'aspect': aspect,
                    'sentiment': 'very_negative',
                    'evidence': ['terrible experience', 'very disappointed'],
                    'opinion_terms': ['terrible', 'disappointing'],
                    'star_rating': 1,
                    'review_date': '2024-10-14',
                    'review_text': 'Terrible experience. Very disappointed with the quality.',
                    'channel': 'TripAdvisor'
                }
            ],
            'positive': [
                {
                    'review_uid': 'review_003',
                    'aspect': aspect,
                    'sentiment': 'positive',
                    'evidence': ['very clean', 'well maintained'],
                    'opinion_terms': ['clean', 'excellent'],
                    'star_rating': 5,
                    'review_date': '2024-10-13',
                    'review_text': 'Everything was very clean and well maintained. Excellent experience!',
                    'channel': 'Google'
                },
                {
                    'review_uid': 'review_004',
                    'aspect': aspect,
                    'sentiment': 'very_positive',
                    'evidence': ['outstanding', 'exceeded expectations'],
                    'opinion_terms': ['outstanding', 'wonderful'],
                    'star_rating': 5,
                    'review_date': '2024-10-12',
                    'review_text': 'Outstanding quality! Exceeded all my expectations. Highly recommend.',
                    'channel': 'Booking.com'
                }
            ]
        }
    
    def get_summary_stats_from_reviews(self, days: Optional[int] = 21) -> Dict:
        """Get summary statistics from review_aspect_details table for HQ dashboard
        
        Args:
            days: Number of days to look back from latest review. If None, use all historical data.
        """
        try:
            # Build WHERE clause based on days parameter
            if days is not None:
                date_filter = f"WHERE review_date >= latest_review_date - INTERVAL {days} DAYS"
            else:
                date_filter = ""  # No date filter for all historical
            
            # Query for overall stats
            query = f"""
            WITH latest_date_cte AS (
                SELECT 
                    MAX(review_date) AS latest_review_date
                FROM {self.reviews_table}
                )
            SELECT 
                COUNT(DISTINCT review_uid) AS total_reviews,
                COUNT(DISTINCT location) AS total_properties,
                AVG(star_rating) AS avg_rating,
                COUNT(CASE WHEN sentiment IN ('negative', 'very_negative') THEN 1 END) AS negative_reviews,
                COUNT(*) AS total_aspects_reviewed,
                MAX(review_date) AS latest_review_date
                FROM {self.reviews_table}
                CROSS JOIN latest_date_cte
                {date_filter}
            """
            
            rows = database_service.query(query, role=self._role, property=self._property)

            if rows and len(rows) > 0:
                row = rows[0]
                # Database returns rows as dictionaries
                total_reviews = int(row['total_reviews']) if row.get('total_reviews') else 0
                negative_reviews = int(row['negative_reviews']) if row.get('negative_reviews') else 0
                total_aspects = int(row['total_aspects_reviewed']) if row.get('total_aspects_reviewed') else 1
                
                # Calculate negative percentage
                negative_percentage = (negative_reviews / total_aspects * 100) if total_aspects > 0 else 0
                
                return {
                    'total_reviews': total_reviews,
                    'total_properties': int(row['total_properties']) if row.get('total_properties') else 0,
                    'avg_rating': float(row['avg_rating']) if row.get('avg_rating') else 4.0,
                    'negative_reviews': negative_reviews,
                    'avg_negative_reviews': round(negative_percentage, 1),
                    'reviews_processed': total_reviews,
                    'latest_review_date': str(row['latest_review_date']) if row.get('latest_review_date') else 'N/A'
                }
            
        except Exception as e:
            print(f"⚠️  Error fetching summary stats: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Return default stats if query fails
        return {
            'total_reviews': 0,
            'total_properties': 0,
            'avg_rating': 0.0,
            'negative_reviews': 0,
            'avg_negative_reviews': 0.0,
            'reviews_processed': 0,
            'latest_review_date': 'N/A'
        }
    
    def get_properties_by_region_and_severity(self) -> Dict:
        """Group flagged properties by geographic region and severity"""
        city_to_region = self._get_city_to_region_mapping()
        
        # flagged = self.get_flagged_properties_grouped()
        flagged = self.get_flagged_properties_grouped()

        if not flagged:
            return {}
        
        # Group by geographic region
        regions = {}
        for prop in flagged:
            # Extract city from location (format: "City, ST")
            location = prop['property']
            city = location.split(',')[0].strip() if ',' in location else location
            
            # Try exact match first
            region = city_to_region.get(city, None)
            
            # If no exact match, try case-insensitive match
            if region is None:
                for mapped_city, mapped_region in city_to_region.items():
                    if mapped_city.lower() == city.lower():
                        region = mapped_region
                        break
            
            if region is None:
                region = 'Other'
            
            if region not in regions:
                regions[region] = {'critical': [], 'warning': []}
            
            severity = prop['severity']
            # severity = prop['status']
            if severity in ['critical', 'warning']:
                regions[region][severity].append(prop)
        
        # Sort regions by total count (descending), with specific order preference
        region_order = ['Northeast', 'Mid-Atlantic', 'Southeast', 'Midwest', 'South', 'Southwest', 'West', 'Other']
        
        # Sort by total issues (descending), but maintain regional grouping
        sorted_regions = {}
        for region_name in region_order:
            if region_name in regions:
                sorted_regions[region_name] = regions[region_name]
        
        # Add any remaining regions not in the order list
        for region_name, data in sorted(regions.items(), key=lambda x: len(x[1]['critical']) + len(x[1]['warning']), reverse=True):
            if region_name not in sorted_regions:
                sorted_regions[region_name] = data
        
        return sorted_regions
    
    def _get_city_to_region_mapping(self) -> Dict:
        """Get the city to region mapping"""
        return {
            # Northeast (20)
            'Boston': 'Northeast', 'Cambridge': 'Northeast', 'Worcester': 'Northeast', 'Springfield': 'Northeast',
            'Providence': 'Northeast', 'Hartford': 'Northeast', 'New Haven': 'Northeast', 'Stamford': 'Northeast',
            'Portland': 'Northeast', 'Bangor': 'Northeast', 'Manchester': 'Northeast', 'Concord': 'Northeast',
            'Burlington': 'Northeast', 'Albany': 'Northeast', 'Syracuse': 'Northeast', 'Rochester': 'Northeast',
            'Buffalo': 'Northeast', 'White Plains': 'Northeast', 'Newark': 'Northeast', 'Jersey City': 'Northeast',
            
            # Mid-Atlantic (20)
            'New York City': 'Mid-Atlantic', 'Manhattan': 'Mid-Atlantic', 'Brooklyn': 'Mid-Atlantic', 'Queens': 'Mid-Atlantic',
            'Long Island': 'Mid-Atlantic', 'Atlantic City': 'Mid-Atlantic', 'Philadelphia': 'Mid-Atlantic', 'Pittsburgh': 'Mid-Atlantic',
            'Harrisburg': 'Mid-Atlantic', 'Allentown': 'Mid-Atlantic', 'Wilmington': 'Mid-Atlantic', 'Baltimore': 'Mid-Atlantic',
            'Annapolis': 'Mid-Atlantic', 'Silver Spring': 'Mid-Atlantic', 'Washington': 'Mid-Atlantic', 'Arlington': 'Mid-Atlantic',
            'Alexandria': 'Mid-Atlantic', 'Richmond': 'Mid-Atlantic', 'Virginia Beach': 'Mid-Atlantic', 'Norfolk': 'Mid-Atlantic',
            'Charlottesville': 'Mid-Atlantic',
            
            # Southeast (20)
            'Charlotte': 'Southeast', 'Raleigh': 'Southeast', 'Durham': 'Southeast', 'Greensboro': 'Southeast',
            'Asheville': 'Southeast', 'Charleston': 'Southeast', 'Columbia': 'Southeast', 'Greenville': 'Southeast',
            'Atlanta': 'Southeast', 'Savannah': 'Southeast', 'Augusta': 'Southeast', 'Orlando': 'Southeast',
            'Tampa': 'Southeast', 'Miami': 'Southeast', 'Fort Lauderdale': 'Southeast', 'West Palm Beach': 'Southeast',
            'Jacksonville': 'Southeast', 'Tallahassee': 'Southeast', 'Pensacola': 'Southeast', 'Key West': 'Southeast',
            
            # Midwest (20)
            'Chicago': 'Midwest', 'Naperville': 'Midwest', 'Springfield': 'Midwest', 'Rockford': 'Midwest',
            'Indianapolis': 'Midwest', 'Fort Wayne': 'Midwest', 'Columbus': 'Midwest', 'Cleveland': 'Midwest',
            'Cincinnati': 'Midwest', 'Toledo': 'Midwest', 'Detroit': 'Midwest', 'Ann Arbor': 'Midwest',
            'Grand Rapids': 'Midwest', 'Milwaukee': 'Midwest', 'Madison': 'Midwest', 'Green Bay': 'Midwest',
            'Minneapolis': 'Midwest', 'St. Paul': 'Midwest', 'Des Moines': 'Midwest', 'Kansas City': 'Midwest',
            
            # South (15)
            'Nashville': 'South', 'Memphis': 'South', 'Knoxville': 'South', 'Chattanooga': 'South',
            'Louisville': 'South', 'Lexington': 'South', 'Birmingham': 'South', 'Montgomery': 'South',
            'Huntsville': 'South', 'New Orleans': 'South', 'Baton Rouge': 'South', 'Little Rock': 'South',
            'Fayetteville': 'South', 'Oklahoma City': 'South', 'Tulsa': 'South',
            
            # Southwest (10)
            'Dallas': 'Southwest', 'Fort Worth': 'Southwest', 'Houston': 'Southwest', 'Austin': 'Southwest',
            'San Antonio': 'Southwest', 'El Paso': 'Southwest', 'Albuquerque': 'Southwest', 'Santa Fe': 'Southwest',
            'Phoenix': 'Southwest', 'Tucson': 'Southwest',
            
            # West (15)
            'Denver': 'West', 'Colorado Springs': 'West', 'Salt Lake City': 'West', 'Park City': 'West',
            'Las Vegas': 'West', 'Reno': 'West', 'Boise': 'West', 'Spokane': 'West',
            'Seattle': 'West', 'Tacoma': 'West', 'Portland': 'West', 'Eugene': 'West',
            'San Diego': 'West', 'Los Angeles': 'West', 'San Francisco': 'West',
        }


# Singleton instance
property_service = PropertyService()
