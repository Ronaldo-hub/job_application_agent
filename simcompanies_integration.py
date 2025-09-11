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

    def generate_discord_message(self, resume_skills: List[str]) -> str:
        """Generate Discord message with business recommendations."""
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
        message += f"Reply with 'Start' to begin business simulation or 'Explore' for more options."

        return message

# Global instance for easy access
simcompanies_client = SimCompaniesIntegration()

def get_simcompanies_recommendations(resume_skills: List[str]) -> Dict:
    """Main function to get Sim Companies recommendations."""
    try:
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
            'discord_message': simcompanies_client.generate_discord_message(resume_skills)
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

if __name__ == "__main__":
    # Test the integration
    test_skills = ['chemical_engineering', 'management', 'finance']
    recommendations = get_simcompanies_recommendations(test_skills)
    print(json.dumps(recommendations, indent=2))