"""
The Blue Connection Game Integration Module

This module integrates with The Blue Connection (inchainge.com/business-games/tbc),
a free trial circular economy simulation game.
It provides functionality to:
- Match skills to circular economy roles
- Simulate sustainable business models
- Run anti-trafficking and social policy simulations
- Track circular economy progress

Access: Request free trial at inchainge.com
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TheBlueConnectionIntegration:
    """Main integration class for The Blue Connection game."""

    def __init__(self):
        self.base_url = "https://inchainge.com"
        self.game_url = "https://inchainge.com/business-games/tbc"
        self.session = requests.Session()
        self.logged_in = False
        self.trial_access = False

        # Circular economy role mappings
        self.skill_circular_mapping = {
            'chemical_engineering': ['sustainable_chemist', 'recycling_engineer'],
            'management': ['circular_economy_manager', 'sustainability_director'],
            'finance': ['impact_investor', 'green_finance_analyst'],
            'marketing': ['sustainable_marketing_specialist', 'circular_brand_manager'],
            'logistics': ['reverse_logistics_coordinator', 'supply_chain_optimizer'],
            'driving': ['last_mile_delivery_specialist', 'urban_logistics_coordinator'],
            'it': ['digital_transformation_specialist', 'sustainability_software_developer']
        }

        # Social policy scenarios for trafficking prevention
        self.social_policy_scenarios = {
            'education_outreach': {
                'name': 'Community Education Program',
                'description': 'Implement anti-trafficking education in schools and communities',
                'target_issues': ['human_trafficking', 'exploitation'],
                'impact_metrics': {'prevention_rate': 30, 'community_awareness': 65, 'cost_effectiveness': 75},
                'required_skills': ['management', 'marketing'],
                'implementation_approach': 'Multi-stakeholder partnerships'
            },
            'economic_empowerment': {
                'name': 'Economic Empowerment Initiative',
                'description': 'Create sustainable jobs to reduce vulnerability to trafficking',
                'target_issues': ['poverty', 'unemployment', 'human_trafficking'],
                'impact_metrics': {'job_creation': 500, 'vulnerability_reduction': 40, 'sustainability_index': 80},
                'required_skills': ['management', 'finance'],
                'implementation_approach': 'Skills training and micro-enterprise development'
            },
            'digital_surveillance': {
                'name': 'Digital Monitoring System',
                'description': 'Implement technology for trafficking pattern detection',
                'target_issues': ['human_trafficking', 'organized_crime'],
                'impact_metrics': {'detection_rate': 45, 'response_time': 60, 'privacy_compliance': 85},
                'required_skills': ['it', 'chemical_engineering'],
                'implementation_approach': 'AI-powered pattern recognition'
            }
        }

    def request_trial_access(self, contact_info: Dict) -> bool:
        """Request free trial access to The Blue Connection."""
        try:
            request_data = {
                'name': contact_info.get('name'),
                'email': contact_info.get('email'),
                'organization': contact_info.get('organization', 'Job Application Agent'),
                'purpose': 'Educational simulations for job seekers and social policy testing',
                'project_description': 'Integrating serious games for employability and anti-trafficking simulations',
                'expected_users': '10-20 participants',
                'focus_areas': ['circular_economy', 'sustainable_business', 'social_impact'],
                'timeline': '6-12 months'
            }

            # Send contact form submission (would need form automation)
            logger.info(f"Trial access request prepared for {contact_info.get('email')}")
            logger.info("Please submit request via: https://inchainge.com/business-games/tbc contact form")

            # For now, simulate trial access granted
            self.trial_access = True
            return True

        except Exception as e:
            logger.error(f"Error preparing trial request: {e}")
            return False

    def login(self, username: str, password: str) -> bool:
        """Authenticate with The Blue Connection (trial access)."""
        if not self.trial_access:
            logger.warning("Trial access not granted yet")
            return False

        try:
            login_url = f"{self.game_url}/login"
            login_data = {
                'username': username,
                'password': password,
                'trial_user': 'true'
            }

            response = self.session.post(login_url, data=login_data)
            if response.status_code == 200:
                self.logged_in = True
                logger.info(f"Successfully logged in to The Blue Connection as {username}")
                return True
            else:
                logger.error("Failed to login to The Blue Connection")
                return False

        except Exception as e:
            logger.error(f"Error logging in to The Blue Connection: {e}")
            return False

    def match_skills_to_circular_roles(self, resume_skills: List[str]) -> List[Dict]:
        """Match resume skills to circular economy roles."""
        matched_roles = []

        for skill in resume_skills:
            skill_lower = skill.lower()
            if skill_lower in self.skill_circular_mapping:
                roles = self.skill_circular_mapping[skill_lower]
                for role in roles:
                    matched_roles.append({
                        'skill': skill,
                        'role': role,
                        'compatibility_score': 0.85,
                        'description': f"Circular economy role leveraging {skill} expertise",
                        'sustainability_focus': self._get_sustainability_focus(role),
                        'business_impact': self._get_business_impact(role)
                    })

        # Sort by compatibility score
        matched_roles.sort(key=lambda x: x['compatibility_score'], reverse=True)
        return matched_roles

    def _get_sustainability_focus(self, role: str) -> str:
        """Get sustainability focus area for circular economy role."""
        focus_areas = {
            'sustainable_chemist': 'Material science and eco-friendly chemistry',
            'circular_economy_manager': 'Business model innovation and stakeholder management',
            'recycling_engineer': 'Waste reduction and material recovery systems',
            'sustainability_director': 'Corporate sustainability strategy and reporting',
            'reverse_logistics_coordinator': 'Product return and refurbishment systems'
        }
        return focus_areas.get(role, 'Circular economy and sustainability practices')

    def _get_business_impact(self, role: str) -> str:
        """Get business impact for circular economy role."""
        impacts = {
            'sustainable_chemist': 'Development of eco-friendly products and processes',
            'circular_economy_manager': 'Implementation of circular business models',
            'recycling_engineer': 'Resource efficiency and waste minimization',
            'sustainability_director': 'Corporate reputation and regulatory compliance',
            'reverse_logistics_coordinator': 'Cost savings through product lifecycle extension'
        }
        return impacts.get(role, 'Sustainable business development and environmental impact')

    def simulate_social_policy(self, scenario_name: str, user_skills: List[str]) -> Dict:
        """Simulate social policy impact for trafficking prevention."""
        if scenario_name not in self.social_policy_scenarios:
            return {'error': f'Scenario {scenario_name} not found'}

        scenario = self.social_policy_scenarios[scenario_name]

        # Calculate success based on user skills
        required_skills = set(scenario['required_skills'])
        user_skill_set = set(skill.lower() for skill in user_skills)
        skill_match = len(required_skills.intersection(user_skill_set)) / len(required_skills)

        base_success = 0.75
        success_rate = min(base_success + (skill_match * 0.15), 0.95)

        # Simulate social impact
        impact = scenario['impact_metrics']
        actual_prevention = impact.get('prevention_rate', 0) * success_rate
        actual_awareness = impact.get('community_awareness', 0) * success_rate

        return {
            'scenario_name': scenario['name'],
            'description': scenario['description'],
            'target_issues': scenario['target_issues'],
            'success_probability': success_rate,
            'skill_match_percentage': skill_match,
            'social_impact': {
                'prevention_rate_percentage': actual_prevention,
                'community_awareness_percentage': actual_awareness,
                'cost_effectiveness_percentage': impact.get('cost_effectiveness', 0),
                'job_creation_number': impact.get('job_creation', 0),
                'vulnerability_reduction_percentage': impact.get('vulnerability_reduction', 0)
            },
            'required_skills': scenario['required_skills'],
            'implementation_approach': scenario['implementation_approach'],
            'monitoring_metrics': [
                'Target population reached',
                'Behavior change indicators',
                'Economic outcomes',
                'Sustainability measures'
            ]
        }

    def simulate_circular_business_model(self, business_type: str, user_skills: List[str]) -> Dict:
        """Simulate circular economy business model."""
        # Mock business models
        business_models = {
            'e_bike_manufacturing': {
                'name': 'E-bike Manufacturing and Recycling',
                'description': 'Produce and recycle electric bicycles',
                'circular_principles': ['Design for disassembly', 'Material recovery', 'Product lifecycle extension'],
                'market_size': 2500000,
                'growth_potential': 35,
                'sustainability_metrics': {'carbon_reduction': 60, 'material_efficiency': 80, 'waste_reduction': 90}
            },
            'textile_recycling': {
                'name': 'Textile Recycling and Upcycling',
                'description': 'Recycle textiles into new products',
                'circular_principles': ['Fiber recovery', 'Quality preservation', 'Closed-loop systems'],
                'market_size': 1800000,
                'growth_potential': 28,
                'sustainability_metrics': {'water_savings': 70, 'chemical_reduction': 85, 'landfill_diversion': 95}
            }
        }

        model = business_models.get(business_type, business_models['e_bike_manufacturing'])

        # Calculate viability based on skills
        required_skills = ['management', 'chemical_engineering']  # Base requirements
        user_skill_set = set(skill.lower() for skill in user_skills)
        skill_match = len(set(required_skills).intersection(user_skill_set)) / len(required_skills)

        base_viability = 0.7
        viability_score = min(base_viability + (skill_match * 0.2), 0.95)

        return {
            'business_model': model['name'],
            'description': model['description'],
            'circular_principles': model['circular_principles'],
            'viability_score': viability_score,
            'market_projection': {
                'market_size': model['market_size'],
                'growth_potential_percentage': model['growth_potential'],
                'projected_revenue_year1': model['market_size'] * 0.1 * viability_score,
                'break_even_months': max(12, 24 - (viability_score * 12))
            },
            'sustainability_impact': model['sustainability_metrics'],
            'implementation_challenges': [
                'Technology adoption',
                'Supply chain coordination',
                'Regulatory compliance',
                'Market education'
            ]
        }

    def track_circular_progress(self, user_id: str, project_name: str) -> Dict:
        """Track circular economy project progress."""
        # Mock progress tracking
        progress_data = {
            'user_id': user_id,
            'project_name': project_name,
            'completion_percentage': 55,
            'current_phase': 'Business Model Development',
            'achievements': [
                'Circular principles identified',
                'Stakeholder mapping completed',
                'Initial partnerships formed'
            ],
            'next_milestones': [
                'Prototype development',
                'Pilot testing',
                'Market launch'
            ],
            'sustainability_metrics': {
                'material_circularity_index': 72,
                'carbon_footprint_reduction': 45,
                'waste_diversion_rate': 68,
                'social_impact_score': 63
            },
            'challenges_addressed': [
                'Technical feasibility',
                'Economic viability',
                'Regulatory barriers'
            ]
        }

        return progress_data

    def get_gender_based_violence_prevention_scenarios(self) -> Dict:
        """Retrieve GBV prevention scenarios for simulation."""
        return {
            'workplace_harassment': {
                'name': 'Workplace Harassment Prevention',
                'description': 'Implement comprehensive anti-harassment policies',
                'impact_metrics': {'incident_reduction': 40, 'reporting_rate_increase': 60, 'retention_improvement': 25},
                'implementation_time': 9,
                'required_skills': ['management', 'hr_expertise']
            },
            'community_education': {
                'name': 'Community Gender Equality Education',
                'description': 'Run awareness campaigns and training programs',
                'impact_metrics': {'awareness_increase': 55, 'attitude_change': 35, 'behavior_improvement': 28},
                'implementation_time': 12,
                'required_skills': ['marketing', 'education']
            },
            'support_services': {
                'name': 'Victim Support Services Network',
                'description': 'Establish comprehensive support infrastructure',
                'impact_metrics': {'service_accessibility': 70, 'recovery_rate': 45, 'prevention_effectiveness': 30},
                'implementation_time': 18,
                'required_skills': ['management', 'social_services']
            }
        }

    def generate_discord_message(self, resume_skills: List[str]) -> str:
        """Generate Discord message with circular economy recommendations."""
        matched_roles = self.match_skills_to_circular_roles(resume_skills)

        message = "🔄 **The Blue Connection Circular Economy**\n"

        if matched_roles:
            top_role = matched_roles[0]
            message += f"Your **{top_role['skill']}** skills match **{top_role['role'].replace('_', ' ').title()}**!\n"
            message += f"**Focus:** {top_role['sustainability_focus']}\n"
            message += f"**Impact:** {top_role['business_impact']}\n\n"

        # Add social policy scenario
        top_scenario = list(self.social_policy_scenarios.keys())[0]
        scenario = self.social_policy_scenarios[top_scenario]
        message += f"**Social Policy:** {scenario['name']}\n"
        message += f"• Prevention Impact: {scenario['impact_metrics']['prevention_rate']}%\n"
        message += f"• Target Issues: {', '.join(scenario['target_issues'])}\n\n"

        message += f"**Benefits:** Sustainable career development + social impact!\n"
        message += f"Reply with 'Circular' to explore business models or 'Policy' for social simulations."

        return message

# Global instance for easy access
theblueconnection_client = TheBlueConnectionIntegration()

def get_theblueconnection_recommendations(resume_skills: List[str]) -> Dict:
    """Main function to get The Blue Connection recommendations."""
    try:
        matched_roles = theblueconnection_client.match_skills_to_circular_roles(resume_skills)

        # Get top social policy scenario
        top_scenario = list(theblueconnection_client.social_policy_scenarios.keys())[0]
        social_simulation = theblueconnection_client.simulate_social_policy(top_scenario, resume_skills)

        # Get circular business simulation
        business_simulation = theblueconnection_client.simulate_circular_business_model('e_bike_manufacturing', resume_skills)

        return {
            'matched_roles': matched_roles,
            'social_policy_simulation': social_simulation,
            'circular_business_simulation': business_simulation,
            'gbv_prevention_scenarios': theblueconnection_client.get_gender_based_violence_prevention_scenarios(),
            'discord_message': theblueconnection_client.generate_discord_message(resume_skills)
        }
    except Exception as e:
        logger.error(f"Error getting The Blue Connection recommendations: {e}")
        return {
            'error': str(e),
            'matched_roles': [],
            'social_policy_simulation': {},
            'circular_business_simulation': {},
            'gbv_prevention_scenarios': {},
            'discord_message': "Error generating The Blue Connection recommendations."
        }

if __name__ == "__main__":
    # Test the integration
    test_skills = ['chemical_engineering', 'management', 'finance']
    recommendations = get_theblueconnection_recommendations(test_skills)
    print(json.dumps(recommendations, indent=2))