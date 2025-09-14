"""
CWetlands Game Integration Module

This module integrates with CWetlands (constructedwetlands.socialsimulations.org),
a free constructed wetlands simulation for environmental management.
It provides functionality to:
- Simulate water scarcity and climate change scenarios
- Match skills to environmental management roles
- Run policy simulations for water conservation
- Track environmental impact metrics

Access: Request moderator account at contact@socialsimulations.org
Offline version available for local simulations
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

class CWetlandsIntegration:
    """Main integration class for CWetlands simulation."""

    def __init__(self):
        self.base_url = "https://constructedwetlands.socialsimulations.org"
        self.offline_mode = True  # Default to offline until API access granted
        self.session = requests.Session()
        self.logged_in = False
        self.user_credentials = None

        # Environmental role mappings for skill matching
        self.skill_environment_mapping = {
            'chemical_engineering': ['water_quality_specialist', 'treatment_engineer'],
            'management': ['environmental_manager', 'project_coordinator'],
            'driving': ['field_technician', 'site_inspector'],
            'finance': ['sustainability_officer', 'grant_manager'],
            'it': ['data_analyst', 'monitoring_system_specialist'],
            'logistics': ['supply_chain_coordinator', 'resource_manager']
        }

        # Water conservation policy scenarios
        self.policy_scenarios = {
            'rainwater_harvesting': {
                'name': 'Rainwater Harvesting Initiative',
                'description': 'Implement community rainwater collection systems',
                'impact_metrics': {'water_savings': 25, 'cost_savings': 15, 'implementation_time': 12},
                'required_skills': ['management', 'chemical_engineering'],
                'success_factors': ['Community engagement', 'Technical expertise', 'Funding availability']
            },
            'greywater_recycling': {
                'name': 'Greywater Recycling Program',
                'description': 'Treat and reuse greywater for non-potable applications',
                'impact_metrics': {'water_savings': 35, 'cost_savings': 20, 'implementation_time': 18},
                'required_skills': ['chemical_engineering', 'it'],
                'success_factors': ['Treatment technology', 'Regulatory compliance', 'Public acceptance']
            },
            'drought_resilient_farming': {
                'name': 'Drought-Resilient Agriculture',
                'description': 'Implement water-efficient farming practices',
                'impact_metrics': {'water_savings': 40, 'cost_savings': 10, 'implementation_time': 24},
                'required_skills': ['management', 'driving'],
                'success_factors': ['Farmer training', 'Technology adoption', 'Market access']
            }
        }

    def request_access(self, contact_info: Dict) -> bool:
        """Request access to CWetlands moderator account."""
        try:
            request_data = {
                'name': contact_info.get('name'),
                'email': contact_info.get('email'),
                'organization': contact_info.get('organization', 'Job Application Agent'),
                'purpose': 'Educational simulations for job seekers in Cape Town',
                'project_description': 'Integrating serious games for employability enhancement',
                'expected_users': '10-20 job seekers',
                'timeline': '6-12 months'
            }

            # Send email request (would need email service integration)
            logger.info(f"Access request prepared for {contact_info.get('email')}")
            logger.info("Please send this request to: contact@socialsimulations.org")

            # For now, return True to indicate request prepared
            return True

        except Exception as e:
            logger.error(f"Error preparing access request: {e}")
            return False

    def login(self, username: str, password: str) -> bool:
        """Authenticate with CWetlands (when access granted)."""
        if self.offline_mode:
            logger.info("Running in offline mode - no login required")
            self.logged_in = True
            return True

        try:
            login_url = f"{self.base_url}/login"
            login_data = {
                'username': username,
                'password': password
            }

            response = self.session.post(login_url, data=login_data)
            if response.status_code == 200:
                self.logged_in = True
                logger.info(f"Successfully logged in to CWetlands as {username}")
                return True
            else:
                logger.error("Failed to login to CWetlands")
                return False

        except Exception as e:
            logger.error(f"Error logging in to CWetlands: {e}")
            return False

    def match_skills_to_environmental_roles(self, resume_skills: List[str]) -> List[Dict]:
        """Match resume skills to environmental management roles."""
        matched_roles = []

        for skill in resume_skills:
            skill_lower = skill.lower()
            if skill_lower in self.skill_environment_mapping:
                roles = self.skill_environment_mapping[skill_lower]
                for role in roles:
                    matched_roles.append({
                        'skill': skill,
                        'role': role,
                        'compatibility_score': 0.8,
                        'description': f"Environmental role applying {skill} expertise",
                        'focus_area': self._get_role_focus(role),
                        'impact_potential': self._get_role_impact(role)
                    })

        # Sort by compatibility score
        matched_roles.sort(key=lambda x: x['compatibility_score'], reverse=True)
        return matched_roles

    def _get_role_focus(self, role: str) -> str:
        """Get focus area for environmental role."""
        focus_areas = {
            'water_quality_specialist': 'Water treatment and quality monitoring',
            'treatment_engineer': 'Wastewater treatment system design',
            'environmental_manager': 'Project management and stakeholder coordination',
            'field_technician': 'Field monitoring and data collection',
            'data_analyst': 'Environmental data analysis and reporting'
        }
        return focus_areas.get(role, 'Environmental management and sustainability')

    def _get_role_impact(self, role: str) -> str:
        """Get impact potential for environmental role."""
        impacts = {
            'water_quality_specialist': 'Direct impact on water quality improvement',
            'treatment_engineer': 'Large-scale water treatment infrastructure',
            'environmental_manager': 'Policy implementation and community engagement',
            'field_technician': 'Ground-level environmental monitoring',
            'data_analyst': 'Data-driven environmental decision making'
        }
        return impacts.get(role, 'Environmental conservation and sustainability')

    def simulate_policy_scenario(self, scenario_name: str, user_skills: List[str]) -> Dict:
        """Simulate environmental policy scenario."""
        if scenario_name not in self.policy_scenarios:
            return {'error': f'Scenario {scenario_name} not found'}

        scenario = self.policy_scenarios[scenario_name]

        # Calculate success based on user skills
        required_skills = set(scenario['required_skills'])
        user_skill_set = set(skill.lower() for skill in user_skills)
        skill_match = len(required_skills.intersection(user_skill_set)) / len(required_skills)

        base_success = 0.7
        success_rate = min(base_success + (skill_match * 0.2), 0.95)

        # Simulate environmental impact
        impact = scenario['impact_metrics']
        actual_savings = impact['water_savings'] * success_rate
        actual_cost_savings = impact['cost_savings'] * success_rate

        return {
            'scenario_name': scenario['name'],
            'description': scenario['description'],
            'success_probability': success_rate,
            'skill_match_percentage': skill_match,
            'environmental_impact': {
                'water_savings_percentage': actual_savings,
                'cost_savings_percentage': actual_cost_savings,
                'implementation_time_months': impact['implementation_time'],
                'co2_reduction_estimate': actual_savings * 0.5  # Rough estimate
            },
            'required_skills': scenario['required_skills'],
            'success_factors': scenario['success_factors'],
            'recommendations': [
                'Conduct community stakeholder analysis',
                'Develop monitoring and evaluation framework',
                'Secure funding and partnerships',
                'Implement phased rollout approach'
            ]
        }

    def run_water_scarcity_simulation(self, location_data: Dict) -> Dict:
        """Run water scarcity simulation for specific location (e.g., Cape Town)."""
        # Mock simulation based on Cape Town water crisis data
        base_water_demand = location_data.get('population', 4000000) * 200  # 200L per person per day
        current_supply = base_water_demand * 0.8  # 80% of demand
        deficit_percentage = ((base_water_demand - current_supply) / base_water_demand) * 100

        return {
            'location': location_data.get('name', 'Cape Town'),
            'water_demand_liters_day': base_water_demand,
            'current_supply_liters_day': current_supply,
            'deficit_percentage': deficit_percentage,
            'critical_threshold': 85,  # Day Zero at 85% deficit
            'days_to_crisis': max(0, (deficit_percentage - 85) * -10),  # Rough estimate
            'recommended_actions': [
                'Implement water restrictions',
                'Accelerate desalination projects',
                'Promote water conservation programs',
                'Develop groundwater resources'
            ],
            'policy_impact_scenarios': {
                'conservation_campaign': {'water_savings': 15, 'timeline': 6},
                'infrastructure_upgrade': {'water_savings': 25, 'timeline': 24},
                'demand_management': {'water_savings': 20, 'timeline': 12}
            }
        }

    def track_environmental_progress(self, user_id: str, project_name: str) -> Dict:
        """Track environmental project progress."""
        # Mock progress tracking
        progress_data = {
            'user_id': user_id,
            'project_name': project_name,
            'completion_percentage': 45,
            'current_phase': 'Planning and Assessment',
            'achievements': [
                'Stakeholder mapping completed',
                'Baseline data collected',
                'Initial funding secured'
            ],
            'next_milestones': [
                'Detailed project design',
                'Regulatory approvals',
                'Community consultation'
            ],
            'environmental_metrics': {
                'water_quality_improvement': 12,
                'biodiversity_impact': 8,
                'community_engagement_score': 75,
                'sustainability_index': 68
            },
            'challenges': [
                'Funding constraints',
                'Regulatory delays',
                'Community resistance'
            ]
        }

        return progress_data

    def get_climate_change_impacts(self) -> Dict:
        """Retrieve climate change impact data for simulations."""
        # Mock climate data for Cape Town region
        return {
            'temperature_increase': 2.1,  # Degrees Celsius by 2050
            'precipitation_change': -15,  # Percentage decrease
            'extreme_weather_events': {
                'drought_frequency': 'Increased by 40%',
                'heatwave_intensity': 'Increased by 25%',
                'storm_surge_risk': 'Moderate increase'
            },
            'water_resources_impact': {
                'dam_capacity_reduction': 20,
                'groundwater_depletion': 15,
                'water_quality_degradation': 10
            },
            'adaptation_strategies': [
                'Water demand management',
                'Alternative water sources',
                'Climate-resilient infrastructure',
                'Ecosystem-based adaptation'
            ]
        }

    def generate_discord_message(self, resume_skills: List[str]) -> str:
        """Generate Discord message with environmental recommendations."""
        matched_roles = self.match_skills_to_environmental_roles(resume_skills)

        message = "🌿 **CWetlands Environmental Simulation**\n"

        if matched_roles:
            top_role = matched_roles[0]
            message += f"Your **{top_role['skill']}** skills match **{top_role['role'].replace('_', ' ').title()}**!\n"
            message += f"**Focus:** {top_role['focus_area']}\n"
            message += f"**Impact:** {top_role['impact_potential']}\n\n"

        # Add policy scenario
        top_scenario = list(self.policy_scenarios.keys())[0]
        scenario = self.policy_scenarios[top_scenario]
        message += f"**Policy Opportunity:** {scenario['name']}\n"
        message += f"• Water Savings: {scenario['impact_metrics']['water_savings']}%\n"
        message += f"• Implementation: {scenario['impact_metrics']['implementation_time']} months\n\n"

        message += f"**Benefits:** Address Cape Town's water crisis + gain environmental expertise!\n"
        message += f"Reply with 'Simulate' to run policy scenario or 'Learn' for more details."

        return message

# Global instance for easy access
cwetlands_client = CWetlandsIntegration()

def get_cwetlands_recommendations(resume_skills: List[str]) -> Dict:
    """Main function to get CWetlands recommendations."""
    try:
        matched_roles = cwetlands_client.match_skills_to_environmental_roles(resume_skills)

        # Get top policy scenario
        top_scenario = list(cwetlands_client.policy_scenarios.keys())[0]
        policy_simulation = cwetlands_client.simulate_policy_scenario(top_scenario, resume_skills)

        # Cape Town water scarcity simulation
        cape_town_data = {'name': 'Cape Town', 'population': 4000000}
        water_simulation = cwetlands_client.run_water_scarcity_simulation(cape_town_data)

        return {
            'matched_roles': matched_roles,
            'policy_simulation': policy_simulation,
            'water_scarcity_simulation': water_simulation,
            'climate_data': cwetlands_client.get_climate_change_impacts(),
            'discord_message': cwetlands_client.generate_discord_message(resume_skills)
        }
    except Exception as e:
        logger.error(f"Error getting CWetlands recommendations: {e}")
        return {
            'error': str(e),
            'matched_roles': [],
            'policy_simulation': {},
            'water_scarcity_simulation': {},
            'climate_data': {},
            'discord_message': "Error generating CWetlands recommendations."
        }

if __name__ == "__main__":
    # Test the integration
    test_skills = ['chemical_engineering', 'management', 'driving']
    recommendations = get_cwetlands_recommendations(test_skills)
    print(json.dumps(recommendations, indent=2))