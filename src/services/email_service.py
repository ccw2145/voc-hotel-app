"""
Email Service - Generates automated email communications for property managers
"""

from typing import Dict, List, Optional
from datetime import datetime


class EmailService:
    """Service for generating property management emails"""
    
    def generate_property_email(self, property_data: Dict) -> Dict:
        """Generate email communication for property issues"""
        
        if not property_data:
            return {
                'error': 'Property data not found',
                'status': 'error'
            }
        
        critical_issues = [aspect for aspect in property_data['aspects'] if aspect['status'] == 'critical']
        warning_issues = [aspect for aspect in property_data['aspects'] if aspect['status'] == 'warning']
        
        if critical_issues or warning_issues:
            return self._generate_issue_email(property_data, critical_issues, warning_issues)
        else:
            return self._generate_positive_email(property_data)
    
    def _generate_issue_email(self, property_data: Dict, critical_issues: List, warning_issues: List) -> Dict:
        """Generate email for properties with issues"""
        
        primary_issue = critical_issues[0] if critical_issues else warning_issues[0]
        severity = 'critical' if critical_issues else 'attention'
        property_name = property_data['name']
        
        # Generate action items based on the issue type
        action_items = self._get_action_items_for_aspect(primary_issue['name'])
        
        email_content = f"""Subject: {'Urgent Action Required' if severity == 'critical' else 'Attention Required'} - {primary_issue['name']} Issues at {property_name} Property

Dear Property Manager,

Our Voice of Customer analytics have identified {'a critical issue' if severity == 'critical' else 'an issue'} requiring {'immediate' if severity == 'critical' else 'prompt'} attention at the {property_name} location.

ISSUE SUMMARY:
- {primary_issue['name']} satisfaction has {'declined to' if severity == 'critical' else 'increased to'} {primary_issue['percentage']}% negative reviews (7-day average)
- This represents {'a significant increase' if severity == 'critical' else 'an increase'} from our target threshold of <2%
- Guest feedback indicates concerns requiring immediate attention

RECOMMENDED ACTIONS:
{self._format_action_items(action_items)}

EXPECTED TIMELINE:
- Immediate: Begin corrective protocols
- Within 48 hours: Complete initial improvements
- Within 1 week: Full implementation and monitoring

Please confirm receipt and provide an action plan by end of business today.

Best regards,
Lakehouse Inn Voice of Customer Analytics Team"""

        return {
            'property_id': property_data['property_id'],
            'property_name': property_name,
            'email_content': email_content,
            'generated_at': datetime.now().isoformat(),
            'status': 'ready_to_send',
            'severity': severity,
            'primary_issue': primary_issue['name']
        }
    
    def _generate_positive_email(self, property_data: Dict) -> Dict:
        """Generate congratulatory email for well-performing properties"""
        
        property_name = property_data['name']
        
        email_content = f"""Subject: Property Performance Update - {property_name}

Dear Property Manager,

Great news! Our Voice of Customer analytics show that {property_name} is performing excellently across all monitored aspects.

PERFORMANCE SUMMARY:
{chr(10).join(f'- {aspect["name"]}: {aspect["percentage"]}% negative reviews (Excellent)' for aspect in property_data['aspects'])}

GUEST SATISFACTION METRICS:
- Average Rating: {property_data.get('avg_rating', 'N/A')}/5.0
- Total Reviews Analyzed: {property_data.get('reviews_count', 'N/A')}
- Overall Performance: Outstanding

Keep up the excellent work! Your team's dedication to guest satisfaction is clearly reflected in these outstanding results.

Best regards,
Lakehouse Inn Voice of Customer Analytics Team"""

        return {
            'property_id': property_data['property_id'],
            'property_name': property_name,
            'email_content': email_content,
            'generated_at': datetime.now().isoformat(),
            'status': 'ready_to_send',
            'severity': 'positive',
            'primary_issue': None
        }
    
    def _get_action_items_for_aspect(self, aspect_name: str) -> List[str]:
        """Get specific action items based on the aspect type"""
        
        action_items_map = {
            'Room Cleanliness': [
                'Schedule immediate housekeeping audit',
                'Review cleaning supply inventory',
                'Implement guest room inspection checklist',
                'Provide refresher training on deep cleaning protocols'
            ],
            'Staff Service': [
                'Conduct staff service training workshop',
                'Implement guest greeting standards',
                'Review response time protocols',
                'Schedule customer service refresher training'
            ],
            'WiFi Connectivity': [
                'Upgrade to enterprise-grade WiFi equipment',
                'Add backup internet service provider',
                'Implement network monitoring system',
                'Test connectivity in all guest areas'
            ],
            'Noise Levels': [
                'Install additional soundproofing materials',
                'Review HVAC noise levels',
                'Implement quiet hours policy',
                'Inspect room-to-room sound isolation'
            ],
            'Amenities': [
                'Audit all guest amenities and facilities',
                'Review maintenance schedules',
                'Update amenity offerings based on guest feedback',
                'Ensure all amenities are properly stocked'
            ]
        }
        
        return action_items_map.get(aspect_name, [
            'Conduct immediate assessment',
            'Implement corrective measures',
            'Monitor progress closely',
            'Follow up with guest feedback analysis'
        ])
    
    def _format_action_items(self, action_items: List[str]) -> str:
        """Format action items as numbered list"""
        return '\n'.join(f'{i+1}. {item}' for i, item in enumerate(action_items))


# Singleton instance
email_service = EmailService()

