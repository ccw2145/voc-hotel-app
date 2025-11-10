"""
Email Service - Generates automated email communications for property managers
"""

from typing import Dict, List, Optional
from datetime import datetime
from .recommendations_service import recommendations_service


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
        """Generate email for properties with issues - mentions all issues but focuses on critical ones"""
        
        primary_issue = critical_issues[0] if critical_issues else warning_issues[0]
        severity = 'critical' if critical_issues else 'attention'
        property_name = property_data['name']
        
        # Get recommendations from runbook (Lakebase)
        recommendations = recommendations_service.generate_recommendations(property_data)
        
        # Build comprehensive issue summary
        all_issues_summary = []
        
        # Critical issues first (detailed)
        if critical_issues:
            all_issues_summary.append("CRITICAL ISSUES (Immediate Action Required):")
            for issue in critical_issues:
                all_issues_summary.append(f"  • {issue['name']}: {issue['percentage']*100:.1f}% negative reviews - CRITICAL")
        
        # Warning issues (brief mention)
        if warning_issues:
            all_issues_summary.append("\nWARNING LEVEL ISSUES (Action Recommended):")
            for issue in warning_issues:
                all_issues_summary.append(f"  • {issue['name']}: {issue['percentage']*100:.1f}% negative reviews - Needs attention")
        
        issues_summary_text = '\n'.join(all_issues_summary)
        
        # Get detailed action plan for the most critical issue
        primary_recommendation = next(
            (rec for rec in recommendations if rec['aspect'] == primary_issue['name']),
            None
        )
        
        # Use runbook data if available, otherwise fallback to generic
        if primary_recommendation:
            action_items = primary_recommendation['action_items']
            action_description = primary_recommendation['action']
            expected_impact = primary_recommendation['expected_impact']
            timeline = primary_recommendation['timeline']
            cost_estimate = primary_recommendation['cost_estimate']
            difficulty = primary_recommendation['difficulty']
        else:
            action_items = self._get_action_items_for_aspect(primary_issue['name'])
            action_description = f"Address {primary_issue['name']} concerns through targeted improvement initiatives"
            expected_impact = f"Improve {primary_issue['name']} satisfaction"
            timeline = "1-2 weeks"
            cost_estimate = "Medium"
            difficulty = "Medium"
        
        # Count total issues
        total_issues = len(critical_issues) + len(warning_issues)
        critical_count = len(critical_issues)
        
        email_content = f"""Subject: {'URGENT' if severity == 'critical' else 'ATTENTION REQUIRED'} - {total_issues} Issue{'s' if total_issues > 1 else ''} Detected at {property_name}

Dear Property Manager,

Our Voice of Customer analytics have identified {total_issues} open issue{'s' if total_issues > 1 else ''} at the {property_name} location{f', including {critical_count} CRITICAL issue{"s" if critical_count > 1 else ""}' if critical_issues else ''} requiring {'immediate' if severity == 'critical' else 'prompt'} attention.

ALL OPEN ISSUES:
{issues_summary_text}

PRIMARY FOCUS: {primary_issue['name']} (CRITICAL PRIORITY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ISSUE DETAILS:
- Negative review rate: {primary_issue['percentage']*100:.1f}% (Target: <2%)
- Status: {primary_issue['status'].upper()}
- Guest feedback indicates this requires immediate corrective action

RECOMMENDED ACTION PLAN:
{action_description}

SPECIFIC ACTION ITEMS FOR {primary_issue['name'].upper()}:
{self._format_action_items(action_items)}

IMPLEMENTATION DETAILS:
- Timeline: {timeline}
- Estimated Cost: {cost_estimate}
- Implementation Difficulty: {difficulty}
- Expected Impact: {expected_impact}

NEXT STEPS:
1. Address the critical {primary_issue['name']} issue immediately using the action plan above
{"2. Schedule follow-up actions for the " + str(len(warning_issues)) + " warning-level issue" + ("s" if len(warning_issues) > 1 else "") if warning_issues else "2. Monitor other aspects to prevent escalation"}
3. Provide status update within 24 hours
4. Submit full action plan by end of business today

Please confirm receipt and commitment to the action plan immediately.

Best regards,
Lakehouse Inn Voice of Customer Analytics Team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated alert based on guest feedback analysis.
For questions, contact: voc-analytics@lakehouseinn.com"""

        return {
            'property_id': property_data['property_id'],
            'property_name': property_name,
            'email_content': email_content,
            'generated_at': datetime.now().isoformat(),
            'status': 'ready_to_send',
            'severity': severity,
            'primary_issue': primary_issue['name'],
            'total_issues': total_issues,
            'critical_count': critical_count
        }
    
    def _generate_positive_email(self, property_data: Dict) -> Dict:
        """Generate congratulatory email for well-performing properties"""
        
        property_name = property_data['name']
        
        email_content = f"""Subject: Property Performance Update - {property_name}

Dear Property Manager,

Great news! Our Voice of Customer analytics show that {property_name} is performing excellently across all monitored aspects.

PERFORMANCE SUMMARY:
{chr(10).join(f'- {aspect["name"]}: {aspect["percentage"]*100:.1f}% negative reviews (Excellent)' for aspect in property_data['aspects'])}

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

