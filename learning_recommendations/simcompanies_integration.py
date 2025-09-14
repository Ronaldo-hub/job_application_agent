"""
Sim Companies Game Integration Module

This module integrates with Sim Companies (simcompanies.com), a free business management simulation.
It provides functionality to:
- Match resume skills to business roles
- Recommend self-employment paths
- Simulate business management scenarios
- Track entrepreneurial progress

Based on community tools: https://github.com/Gunak/SimCompanies
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

class SimCompaniesIntegration:
    """Main integration class for Sim Companies game."""

    def __init__(self):
        self.base_url = "https://www.simcompanies.com"
        self.api_base = "https://www.simcompanies.com/api"
        self.session = requests.Session()
        self.logged_in = False
        self.user_data = None

        # Business role mappings for skill matching
        self.skill_business_mapping = {
            'chemical_engineering': ['chemical_plant_manager', 'refinery_operator'],
            'management': ['ceo', 'operations_director'],
            'finance': ['cfo', 'financial_analyst'],
            'marketing': ['marketing_director', 'sales_manager'],
            'logistics': ['supply_chain_manager', 'warehouse_manager'],
            'it': ['it_director', 'systems_analyst'],
            'driving': ['transportation_manager', 'fleet_coordinator']
        }

        # Self-employment business templates
        self.business_templates = {
            'retail': {
                'name': 'Virtual Retail Store',
                'startup_cost': 50000,
                'monthly_revenue': 15000,
                'skills_required': ['marketing', 'management'],
                'description': 'Start and manage an online retail business'
            },
            'manufacturing': {
                'name': 'Chemical Processing Plant',
                'startup_cost': 200000,
                'monthly_revenue': 35000,
                'skills_required': ['chemical_engineering', 'management'],
                'description': 'Build and operate a chemical manufacturing facility'
            },
            'logistics': {
                'name': 'Delivery Service Company',
                'startup_cost': 75000,
                'monthly_revenue': 25000,
                'skills_required': ['driving', 'logistics', 'management'],
                'description': 'Manage a transportation and delivery network'
            }
        }

        # Group collaboration business templates
        self.group_business_templates = {
            'community_water_solutions': {
                'name': 'Community Water Solutions Co-op',
                'startup_cost': 150000,
                'monthly_revenue': 45000,
                'skills_required': ['chemical_engineering', 'management', 'logistics', 'marketing'],
                'team_size': 4,
                'roles': {
                    'ceo': ['management'],
                    'operations_director': ['chemical_engineering', 'logistics'],
                    'marketing_director': ['marketing'],
                    'supply_chain_manager': ['logistics']
                },
                'description': 'Collaborative business addressing Cape Town water challenges through innovative solutions',
                'community_impact': 'Water conservation and access solutions'
            },
            'sustainable_manufacturing': {
                'name': 'Green Manufacturing Collective',
                'startup_cost': 300000,
                'monthly_revenue': 60000,
                'skills_required': ['chemical_engineering', 'management', 'finance', 'it'],
                'team_size': 4,
                'roles': {
                    'ceo': ['management'],
                    'cfo': ['finance'],
                    'operations_director': ['chemical_engineering'],
                    'it_director': ['it']
                },
                'description': 'Sustainable manufacturing business combining skills for eco-friendly production',
                'community_impact': 'Environmental sustainability and green jobs'
            },
            'community_services_network': {
                'name': 'Local Services Hub',
                'startup_cost': 100000,
                'monthly_revenue': 30000,
                'skills_required': ['management', 'marketing', 'logistics', 'driving'],
                'team_size': 4,
                'roles': {
                    'ceo': ['management'],
                    'operations_director': ['logistics'],
                    'marketing_director': ['marketing'],
                    'transportation_manager': ['driving']
                },
                'description': 'Community services business providing local solutions and employment',
                'community_impact': 'Local economic development and service provision'
            }
        }

    def login(self, username: str, password: str) -> bool:
        """Authenticate with Sim Companies."""
        try:
            login_url = f"{self.base_url}/login"
            login_data = {
                'username': username,
                'password': password,
                'remember': 'true'
            }

            response = self.session.post(login_url, data=login_data)
            if response.status_code == 200 and 'dashboard' in response.url:
                self.logged_in = True
                logger.info(f"Successfully logged in to Sim Companies as {username}")
                return True
            else:
                logger.error("Failed to login to Sim Companies")
                return False

        except Exception as e:
            logger.error(f"Error logging in to Sim Companies: {e}")
            return False

    def get_user_data(self) -> Optional[Dict]:
        """Retrieve current user and company information."""
        if not self.logged_in:
            logger.error("Not logged in to Sim Companies")
            return None

        try:
            # Get user profile data
            profile_url = f"{self.api_base}/user/profile"
            response = self.session.get(profile_url)

            if response.status_code == 200:
                self.user_data = response.json()
                return self.user_data
            else:
                logger.error("Failed to retrieve user data")
                return None

        except Exception as e:
            logger.error(f"Error retrieving user data: {e}")
            return None

    def get_market_data(self) -> Dict:
        """Retrieve current market data and trends."""
        try:
            market_url = f"{self.api_base}/market/overview"
            response = self.session.get(market_url)

            if response.status_code == 200:
                return response.json()
            else:
                # Return mock data if API unavailable
                return self._get_mock_market_data()

        except Exception as e:
            logger.error(f"Error retrieving market data: {e}")
            return self._get_mock_market_data()

    def _get_mock_market_data(self) -> Dict:
        """Return mock market data for testing."""
        return {
            'commodities': {
                'chemicals': {'price': 45.50, 'trend': 'up', 'demand': 'high'},
                'electronics': {'price': 120.00, 'trend': 'stable', 'demand': 'medium'},
                'machinery': {'price': 85.75, 'trend': 'down', 'demand': 'low'}
            },
            'market_conditions': 'Competitive with high demand for skilled managers',
            'salary_trends': {
                'ceo': 150000,
                'operations_director': 95000,
                'chemical_engineer': 78000
            }
        }

    def match_skills_to_business_roles(self, resume_skills: List[str]) -> List[Dict]:
        """Match resume skills to Sim Companies business roles."""
        matched_roles = []

        for skill in resume_skills:
            skill_lower = skill.lower()
            if skill_lower in self.skill_business_mapping:
                roles = self.skill_business_mapping[skill_lower]
                for role in roles:
                    matched_roles.append({
                        'skill': skill,
                        'role': role,
                        'compatibility_score': 0.85,
                        'description': f"Business role leveraging your {skill} expertise",
                        'salary_range': self._get_role_salary(role),
                        'career_path': self._get_career_path(role)
                    })

        # Sort by compatibility score
        matched_roles.sort(key=lambda x: x['compatibility_score'], reverse=True)
        return matched_roles

    def _get_role_salary(self, role: str) -> Dict:
        """Get salary information for a business role."""
        salary_data = {
            'ceo': {'min': 120000, 'max': 200000, 'avg': 150000},
            'operations_director': {'min': 80000, 'max': 130000, 'avg': 95000},
            'chemical_plant_manager': {'min': 70000, 'max': 110000, 'avg': 85000},
            'cfo': {'min': 90000, 'max': 150000, 'avg': 115000}
        }
        return salary_data.get(role, {'min': 50000, 'max': 80000, 'avg': 60000})

    def _get_career_path(self, role: str) -> List[str]:
        """Get career progression path for a role."""
        career_paths = {
            'ceo': ['Junior Manager', 'Senior Manager', 'Director', 'CEO'],
            'operations_director': ['Supervisor', 'Manager', 'Senior Manager', 'Director'],
            'chemical_plant_manager': ['Technician', 'Engineer', 'Senior Engineer', 'Manager']
        }
        return career_paths.get(role, ['Entry Level', 'Mid Level', 'Senior Level'])

    def recommend_self_employment(self, resume_skills: List[str]) -> List[Dict]:
        """Recommend self-employment business opportunities."""
        recommendations = []

        for business_type, template in self.business_templates.items():
            # Check if user has required skills
            required_skills = set(template['skills_required'])
            user_skills = set(skill.lower() for skill in resume_skills)
            skill_match = len(required_skills.intersection(user_skills)) / len(required_skills)

            if skill_match >= 0.5:  # At least 50% skill match
                recommendations.append({
                    'business_type': business_type,
                    'business_name': template['name'],
                    'description': template['description'],
                    'startup_cost': template['startup_cost'],
                    'monthly_revenue': template['monthly_revenue'],
                    'skill_match_percentage': skill_match,
                    'required_skills': template['skills_required'],
                    'profit_margin': (template['monthly_revenue'] * 12 - template['startup_cost']) / (template['startup_cost'] + template['monthly_revenue'] * 12),
                    'timeline': '3-6 months to profitability'
                })

        # Sort by skill match and profit potential
        recommendations.sort(key=lambda x: (x['skill_match_percentage'], x['profit_margin']), reverse=True)
        return recommendations

    def recommend_group_collaboration(self, group_skills: List[List[str]]) -> List[Dict]:
        """Recommend group business opportunities based on combined skills from multiple people."""
        recommendations = []

        # Combine all skills from the group
        all_skills = set()
        for member_skills in group_skills:
            all_skills.update(skill.lower() for skill in member_skills)

        for business_type, template in self.group_business_templates.items():
            required_skills = set(template['skills_required'])
            skill_match = len(required_skills.intersection(all_skills)) / len(required_skills)
            team_size_match = len(group_skills) / template['team_size']

            if skill_match >= 0.7 and team_size_match >= 0.75:  # Strong skill match and adequate team size
                # Calculate role assignments
                role_assignments = self._assign_roles_to_group(group_skills, template['roles'])

                recommendations.append({
                    'business_type': business_type,
                    'business_name': template['name'],
                    'description': template['description'],
                    'community_impact': template['community_impact'],
                    'startup_cost': template['startup_cost'],
                    'monthly_revenue': template['monthly_revenue'],
                    'skill_match_percentage': skill_match,
                    'team_size_match': team_size_match,
                    'required_skills': template['skills_required'],
                    'available_skills': list(all_skills),
                    'role_assignments': role_assignments,
                    'profit_margin': (template['monthly_revenue'] * 12 - template['startup_cost']) / (template['startup_cost'] + template['monthly_revenue'] * 12),
                    'timeline': '6-12 months to profitability',
                    'collaboration_benefits': [
                        'Shared startup costs and risks',
                        'Complementary skill utilization',
                        'Community problem-solving focus',
                        'Collective entrepreneurship experience'
                    ]
                })

        # Sort by skill match, team fit, and profit potential
        recommendations.sort(key=lambda x: (x['skill_match_percentage'], x['team_size_match'], x['profit_margin']), reverse=True)
        return recommendations

    def _assign_roles_to_group(self, group_skills: List[List[str]], role_requirements: Dict) -> Dict:
        """Assign roles to group members based on their skills."""
        assignments = {}
        used_members = set()

        for role, required_skills in role_requirements.items():
            best_member = None
            best_match = 0

            for i, member_skills in enumerate(group_skills):
                if i in used_members:
                    continue

                member_skill_set = set(skill.lower() for skill in member_skills)
                required_set = set(required_skills)
                match_score = len(required_set.intersection(member_skill_set)) / len(required_set)

                if match_score > best_match:
                    best_match = match_score
                    best_member = i

            if best_member is not None:
                assignments[role] = {
                    'member_index': best_member,
                    'assigned_skills': group_skills[best_member],
                    'match_score': best_match
                }
                used_members.add(best_member)
            else:
                assignments[role] = {
                    'member_index': None,
                    'assigned_skills': [],
                    'match_score': 0,
                    'note': 'No suitable member found - training recommended'
                }

        return assignments

    def simulate_business_scenario(self, business_type: str, user_skills: List[str]) -> Dict:
        """Simulate business performance based on user skills."""
        template = self.business_templates.get(business_type, self.business_templates['retail'])

        # Calculate success factors
        skill_bonus = len(user_skills) * 0.03
        base_success = 0.65
        success_rate = min(base_success + skill_bonus, 0.90)

        # Simulate 12-month performance
        monthly_revenue = template['monthly_revenue']
        monthly_expenses = monthly_revenue * 0.6  # 60% expense ratio
        monthly_profit = monthly_revenue - monthly_expenses

        return {
            'business_type': business_type,
            'success_probability': success_rate,
            'year_1_projections': {
                'total_revenue': monthly_revenue * 12,
                'total_expenses': monthly_expenses * 12,
                'total_profit': monthly_profit * 12,
                'roi_percentage': (monthly_profit * 12 / template['startup_cost']) * 100
            },
            'key_success_factors': [
                'Strong management skills',
                'Market timing',
                'Operational efficiency',
                'Customer acquisition'
            ],
            'risks': [
                'Market competition',
                'Economic downturns',
                'Supply chain disruptions'
            ]
        }

    def simulate_group_business_scenario(self, business_type: str, group_skills: List[List[str]]) -> Dict:
        """Simulate collaborative business performance based on group skills."""
        template = self.group_business_templates.get(business_type)
        if not template:
            return {'error': f'Group business type {business_type} not found'}

        # Calculate group success factors
        total_skills = sum(len(member_skills) for member_skills in group_skills)
        skill_bonus = total_skills * 0.02  # Slightly different scaling for groups
        collaboration_bonus = len(group_skills) * 0.05  # Bonus for team size
        base_success = 0.70  # Higher base for collaborative ventures
        success_rate = min(base_success + skill_bonus + collaboration_bonus, 0.95)

        # Simulate enhanced performance due to collaboration
        monthly_revenue = template['monthly_revenue']
        # Lower expense ratio due to shared resources and complementary skills
        monthly_expenses = monthly_revenue * 0.55
        monthly_profit = monthly_revenue - monthly_expenses

        # Calculate role efficiency bonus
        role_assignments = self._assign_roles_to_group(group_skills, template['roles'])
        filled_roles = sum(1 for assignment in role_assignments.values() if assignment['member_index'] is not None)
        role_efficiency = filled_roles / len(template['roles'])
        efficiency_bonus = role_efficiency * 0.1
        monthly_revenue *= (1 + efficiency_bonus)

        return {
            'business_type': business_type,
            'success_probability': success_rate,
            'team_size': len(group_skills),
            'role_fulfillment': role_efficiency,
            'year_1_projections': {
                'total_revenue': monthly_revenue * 12,
                'total_expenses': monthly_expenses * 12,
                'total_profit': monthly_profit * 12,
                'roi_percentage': (monthly_profit * 12 / template['startup_cost']) * 100,
                'profit_per_member': (monthly_profit * 12) / len(group_skills)
            },
            'collaboration_advantages': [
                'Shared startup costs and risks',
                'Complementary skill utilization',
                'Enhanced problem-solving capacity',
                'Community impact focus',
                'Collective learning and growth'
            ],
            'key_success_factors': [
                'Effective role assignment based on skills',
                'Strong team communication and coordination',
                'Shared vision for community impact',
                'Balanced skill distribution',
                'Collaborative decision-making'
            ],
            'risks': [
                'Team coordination challenges',
                'Skill gaps in key roles',
                'Decision-making conflicts',
                'Unequal contribution perception',
                'Market competition'
            ],
            'community_impact_metrics': {
                'jobs_created_potential': len(group_skills) + 5,  # Team + additional hires
                'local_problem_addressed': template['community_impact'],
                'sustainability_score': 0.85,
                'social_value_created': monthly_revenue * 0.15  # Estimated social value
            }
        }

    def track_entrepreneurial_progress(self, user_id: str, business_type: str) -> Dict:
        """Track entrepreneurial progress and achievements."""
        # Mock progress tracking
        progress_data = {
            'user_id': user_id,
            'business_type': business_type,
            'completion_percentage': 60,
            'current_stage': 'Setup and Planning',
            'achievements': [
                'Business plan completed',
                'Initial funding secured',
                'Team assembled'
            ],
            'next_milestones': [
                'Launch operations',
                'First profitable month',
                'Scale to multiple locations'
            ],
            'performance_metrics': {
                'customer_satisfaction': 4.2,
                'operational_efficiency': 78,
                'profit_margin': 15.5
            }
        }

        return progress_data

    def generate_discord_message(self, resume_skills: List[str], is_group: bool = False, group_skills: List[List[str]] = None) -> str:
        """Generate Discord message with business recommendations."""
        if is_group and group_skills:
            return self._generate_group_discord_message(group_skills)

        matched_roles = self.match_skills_to_business_roles(resume_skills)
        self_employment = self.recommend_self_employment(resume_skills)

        message = "🏢 **Sim Companies Business Recommendation**\n"

        if matched_roles:
            top_role = matched_roles[0]
            salary = top_role['salary_range']
            message += f"Your **{top_role['skill']}** skills match **{top_role['role'].replace('_', ' ').title()}**!\n"
            message += f"**Salary Range:** R{salary['min']:,} - R{salary['max']:,} (Avg: R{salary['avg']:,})\n\n"

        if self_employment:
            top_business = self_employment[0]
            message += f"**Self-Employment Opportunity:**\n"
            message += f"**{top_business['business_name']}**\n"
            message += f"• Startup Cost: R{top_business['startup_cost']:,}\n"
            message += f"• Monthly Revenue: R{top_business['monthly_revenue']:,}\n"
            message += f"• Skill Match: {top_business['skill_match_percentage']:.1%}\n\n"

        message += f"**Benefits:** Gain business management experience + entrepreneurial skills!\n"
        message += f"**Group Option:** If collaborating with others, use 'Group' to explore team business opportunities.\n"
        message += f"Reply with 'Start' to begin business simulation or 'Explore' for more options."

        return message

    def _generate_group_discord_message(self, group_skills: List[List[str]]) -> str:
        """Generate Discord message for group collaboration recommendations."""
        group_recommendations = self.recommend_group_collaboration(group_skills)

        message = "🤝 **Group Collaboration Business Recommendation**\n"
        message += f"**Team Size:** {len(group_skills)} members\n\n"

        if group_recommendations:
            top_business = group_recommendations[0]
            message += f"**Recommended Collaborative Business:**\n"
            message += f"**{top_business['business_name']}**\n"
            message += f"• Community Impact: {top_business['community_impact']}\n"
            message += f"• Startup Cost: R{top_business['startup_cost']:,} (shared)\n"
            message += f"• Monthly Revenue: R{top_business['monthly_revenue']:,}\n"
            message += f"• Skill Match: {top_business['skill_match_percentage']:.1%}\n"
            message += f"• Team Fit: {top_business['team_size_match']:.1%}\n\n"

            # Show role assignments
            message += "**Role Assignments:**\n"
            for role, assignment in top_business['role_assignments'].items():
                if assignment['member_index'] is not None:
                    message += f"• {role.replace('_', ' ').title()}: Member {assignment['member_index'] + 1} ({assignment['match_score']:.1%} match)\n"
                else:
                    message += f"• {role.replace('_', ' ').title()}: ⚠️ Training needed\n"

            message += "\n**Collaboration Benefits:**\n"
            for benefit in top_business['collaboration_benefits'][:3]:
                message += f"• {benefit}\n"

        else:
            message += "❌ **No strong group business matches found.**\n"
            message += "Consider adding team members with complementary skills or exploring individual opportunities.\n"

        message += f"\n**Benefits:** Build community-focused businesses + develop teamwork skills!\n"
        message += f"Reply with 'Start_Group' to begin collaborative business simulation."

        return message

# Global instance for easy access
simcompanies_client = SimCompaniesIntegration()

def get_simcompanies_recommendations(resume_skills: List[str], is_group: bool = False, group_skills: List[List[str]] = None) -> Dict:
    """Main function to get Sim Companies recommendations."""
    try:
        if is_group and group_skills:
            return get_group_simcompanies_recommendations(group_skills)

        matched_roles = simcompanies_client.match_skills_to_business_roles(resume_skills)
        self_employment = simcompanies_client.recommend_self_employment(resume_skills)

        # Get top business simulation
        top_business = self_employment[0] if self_employment else None
        business_simulation = None
        if top_business:
            business_simulation = simcompanies_client.simulate_business_scenario(
                top_business['business_type'], resume_skills
            )

        return {
            'matched_roles': matched_roles,
            'self_employment_opportunities': self_employment,
            'business_simulation': business_simulation,
            'discord_message': simcompanies_client.generate_discord_message(resume_skills, is_group=False)
        }
    except Exception as e:
        logger.error(f"Error getting Sim Companies recommendations: {e}")
        return {
            'error': str(e),
            'matched_roles': [],
            'self_employment_opportunities': [],
            'business_simulation': None,
            'discord_message': "Error generating Sim Companies recommendations."
        }

def get_group_simcompanies_recommendations(group_skills: List[List[str]]) -> Dict:
    """Main function to get group Sim Companies recommendations."""
    try:
        group_recommendations = simcompanies_client.recommend_group_collaboration(group_skills)

        # Get top group business simulation
        top_business = group_recommendations[0] if group_recommendations else None
        group_simulation = None
        if top_business:
            group_simulation = simcompanies_client.simulate_group_business_scenario(
                top_business['business_type'], group_skills
            )

        return {
            'group_recommendations': group_recommendations,
            'group_simulation': group_simulation,
            'team_size': len(group_skills),
            'combined_skills': list(set(skill.lower() for member_skills in group_skills for skill in member_skills)),
            'discord_message': simcompanies_client.generate_discord_message([], is_group=True, group_skills=group_skills)
        }
    except Exception as e:
        logger.error(f"Error getting group Sim Companies recommendations: {e}")
        return {
            'error': str(e),
            'group_recommendations': [],
            'group_simulation': None,
            'discord_message': "Error generating group Sim Companies recommendations."
        }

if __name__ == "__main__":
    # Test individual recommendations
    print("=== Individual Recommendations ===")
    test_skills = ['chemical_engineering', 'management', 'finance']
    recommendations = get_simcompanies_recommendations(test_skills)
    print(json.dumps(recommendations, indent=2))

    # Test group recommendations
    print("\n=== Group Recommendations ===")
    group_skills = [
        ['chemical_engineering', 'management'],  # Member 1
        ['finance', 'marketing'],                # Member 2
        ['logistics', 'driving'],                # Member 3
        ['it', 'marketing']                      # Member 4
    ]
    group_recommendations = get_group_simcompanies_recommendations(group_skills)
    print(json.dumps(group_recommendations, indent=2))