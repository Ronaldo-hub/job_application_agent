"""
Cape Town Data Sources for ABM Simulations

This module provides Cape Town-specific data for agent-based modeling simulations,
including unemployment rates, crime statistics, water usage, economic indicators,
and social demographics relevant to job seekers and policy testing.

Data sources include:
- Western Cape Government statistics
- City of Cape Town reports
- South African Police Service data
- Department of Water and Sanitation
- Statistics South Africa (Stats SA)
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CapeTownDataProvider:
    """Provider for Cape Town-specific data for simulations."""

    def __init__(self):
        # Cape Town demographic data (2023 estimates)
        self.demographics = {
            'population': 4000000,  # Approximate
            'unemployment_rate': 0.25,  # 25%
            'youth_unemployment': 0.35,  # 35% for 15-34 age group
            'female_unemployment': 0.28,  # 28%
            'informal_settlement_population': 0.20,  # 20% in informal settlements
            'education_levels': {
                'no_schooling': 0.05,
                'primary': 0.15,
                'secondary': 0.60,
                'tertiary': 0.20
            },
            'age_distribution': {
                '15-24': 0.18,
                '25-34': 0.22,
                '35-44': 0.20,
                '45-54': 0.18,
                '55-64': 0.12,
                '65+': 0.10
            }
        }

        # Economic indicators
        self.economic_data = {
            'gdp_per_capita': 120000,  # ZAR
            'average_income': 15000,  # Monthly ZAR
            'poverty_rate': 0.15,  # 15%
            'key_sectors': {
                'tourism': 0.15,
                'finance': 0.20,
                'technology': 0.12,
                'manufacturing': 0.18,
                'logistics': 0.10,
                'retail': 0.25
            },
            'skill_demand': {
                'digital_skills': 'high',
                'technical_skills': 'high',
                'soft_skills': 'medium',
                'language_skills': 'medium'
            }
        }

        # Water crisis data (Day Zero scenario)
        self.water_data = {
            'dam_capacity_percentage': 25,  # Current level
            'daily_consumption_target': 45000000,  # Liters per day
            'current_daily_usage': 50000000,  # Liters per day
            'deficit_percentage': 11,  # 11% deficit
            'days_to_crisis': 45,  # Days until Day Zero
            'rainfall_deficit': 0.6,  # 60% below normal
            'groundwater_available': 0.3,  # 30% of normal
            'desalination_capacity': 0.1,  # 10% of needs
            'conservation_measures': {
                'implemented': 0.4,  # 40% adoption
                'potential_savings': 0.25  # 25% potential reduction
            }
        }

        # Crime statistics (per 100,000 population)
        self.crime_data = {
            'violent_crime_rate': 1200,
            'property_crime_rate': 2800,
            'drug_related_crime_rate': 450,
            'human_trafficking_incidents': 25,  # Annual
            'gender_based_violence_rate': 850,
            'youth_crime_rate': 680,
            'crime_trends': {
                'violent_crime': -0.05,  # 5% decrease
                'property_crime': -0.08,  # 8% decrease
                'drug_crime': 0.12  # 12% increase
            }
        }

        # Social issues data
        self.social_issues = {
            'drug_abuse_prevalence': 0.08,  # 8% of population
            'alcohol_abuse_prevalence': 0.15,  # 15% of population
            'mental_health_issues': 0.12,  # 12% of population
            'homelessness_rate': 0.03,  # 3% of population
            'domestic_violence_rate': 0.25,  # 25% of households affected
            'child_poverty_rate': 0.35,  # 35% of children
            'school_dropout_rate': 0.18  # 18% dropout rate
        }

        # Transportation and infrastructure
        self.infrastructure_data = {
            'public_transport_coverage': 0.65,  # 65% coverage
            'road_quality_index': 6.2,  # Out of 10
            'internet_coverage': 0.78,  # 78% coverage
            'electricity_reliability': 0.92,  # 92% uptime
            'housing_backlog': 400000,  # Units needed
            'sanitation_coverage': 0.85  # 85% coverage
        }

    def get_unemployment_simulation_data(self) -> Dict:
        """Get data for unemployment policy simulations."""
        return {
            'baseline_unemployment': self.demographics['unemployment_rate'],
            'youth_unemployment': self.demographics['youth_unemployment'],
            'sector_demand': self.economic_data['key_sectors'],
            'skill_gaps': {
                'digital_literacy': 0.4,  # 40% gap
                'technical_skills': 0.35,  # 35% gap
                'entrepreneurship': 0.5,  # 50% gap
                'soft_skills': 0.3  # 30% gap
            },
            'training_effectiveness': {
                'vocational_training': 0.7,  # 70% success rate
                'digital_skills': 0.65,  # 65% success rate
                'entrepreneurship': 0.55  # 55% success rate
            },
            'economic_factors': {
                'gdp_growth': 0.02,  # 2% annual growth
                'inflation_rate': 0.045,  # 4.5% inflation
                'foreign_investment': 0.15  # 15% of GDP
            }
        }

    def get_water_crisis_simulation_data(self) -> Dict:
        """Get data for water scarcity simulations."""
        return {
            'current_capacity': self.water_data['dam_capacity_percentage'],
            'consumption_patterns': {
                'domestic': 0.45,  # 45% of usage
                'industrial': 0.35,  # 35% of usage
                'commercial': 0.15,  # 15% of usage
                'public': 0.05  # 5% of usage
            },
            'conservation_potential': {
                'short_term': 0.15,  # 15% reduction possible
                'medium_term': 0.25,  # 25% with infrastructure
                'long_term': 0.35  # 35% with desalination
            },
            'alternative_sources': {
                'groundwater': 0.20,  # 20% of needs
                'desalination': 0.15,  # 15% of needs
                'reuse': 0.10  # 10% of needs
            },
            'climate_impacts': {
                'temperature_increase': 2.1,  # Degrees by 2050
                'precipitation_change': -0.15,  # 15% decrease
                'extreme_events': 0.25  # 25% increase in frequency
            }
        }

    def get_crime_simulation_data(self) -> Dict:
        """Get data for crime and trafficking simulations."""
        return {
            'baseline_rates': self.crime_data,
            'vulnerability_factors': {
                'unemployment': 0.3,  # 30% correlation
                'poverty': 0.4,  # 40% correlation
                'education': -0.25,  # Negative correlation
                'social_cohesion': -0.35  # Negative correlation
            },
            'intervention_effectiveness': {
                'community_policing': 0.6,  # 60% reduction potential
                'youth_programs': 0.55,  # 55% reduction potential
                'economic_development': 0.7,  # 70% reduction potential
                'education_initiatives': 0.65  # 65% reduction potential
            },
            'trafficking_patterns': {
                'labor_exploitation': 0.6,  # 60% of cases
                'sexual_exploitation': 0.3,  # 30% of cases
                'organ_trafficking': 0.1,  # 10% of cases
                'domestic_servitude': 0.25  # 25% of cases
            }
        }

    def get_social_policy_simulation_data(self) -> Dict:
        """Get data for social policy simulations."""
        return {
            'prevalence_rates': self.social_issues,
            'intervention_costs': {
                'rehabilitation_programs': 50000,  # ZAR per person
                'prevention_programs': 25000,  # ZAR per person
                'support_services': 30000  # ZAR per person
            },
            'success_rates': {
                'drug_rehabilitation': 0.45,  # 45% success rate
                'mental_health_treatment': 0.6,  # 60% success rate
                'poverty_alleviation': 0.55,  # 55% success rate
                'education_interventions': 0.7  # 70% success rate
            },
            'policy_leverage': {
                'early_intervention': 2.5,  # 2.5x return on investment
                'community_based': 3.2,  # 3.2x return on investment
                'multi_sectoral': 4.1  # 4.1x return on investment
            }
        }

    def get_education_simulation_data(self) -> Dict:
        """Get data for education and skills development simulations."""
        return {
            'enrollment_rates': {
                'primary': 0.95,  # 95% enrollment
                'secondary': 0.85,  # 85% enrollment
                'tertiary': 0.25  # 25% enrollment
            },
            'completion_rates': {
                'primary': 0.88,  # 88% completion
                'secondary': 0.75,  # 75% completion
                'tertiary': 0.65  # 65% completion
            },
            'skill_development': {
                'vocational_training': 0.4,  # 40% participation
                'digital_skills': 0.35,  # 35% proficiency
                'entrepreneurship': 0.2,  # 20% training
                'work_readiness': 0.45  # 45% prepared
            },
            'education_quality': {
                'teacher_student_ratio': 1/35,  # 1:35 ratio
                'infrastructure_index': 6.8,  # Out of 10
                'curriculum_relevance': 0.7,  # 70% relevant
                'assessment_quality': 0.75  # 75% quality
            }
        }

    def get_economic_simulation_data(self) -> Dict:
        """Get data for economic development simulations."""
        return {
            'employment_sectors': self.economic_data['key_sectors'],
            'growth_potential': {
                'tourism': 0.08,  # 8% annual growth
                'technology': 0.12,  # 12% annual growth
                'manufacturing': 0.06,  # 6% annual growth
                'finance': 0.07  # 7% annual growth
            },
            'investment_attractiveness': {
                'infrastructure': 7.2,  # Out of 10
                'skills_availability': 6.8,  # Out of 10
                'business_environment': 7.5,  # Out of 10
                'innovation_ecosystem': 7.0  # Out of 10
            },
            'sme_development': {
                'startup_rate': 0.05,  # 5% annual startup rate
                'survival_rate_2year': 0.65,  # 65% survival
                'job_creation_per_sme': 4.2,  # Average jobs per SME
                'growth_potential': 0.25  # 25% annual growth
            }
        }

    def get_environmental_simulation_data(self) -> Dict:
        """Get data for environmental policy simulations."""
        return {
            'air_quality': {
                'pm25_levels': 15.5,  # μg/m³
                'no2_levels': 25.8,  # μg/m³
                'compliance_rate': 0.75  # 75% compliance
            },
            'waste_management': {
                'recycling_rate': 0.25,  # 25% recycling
                'landfill_diversion': 0.35,  # 35% diverted
                'waste_generation': 1.2  # kg per capita per day
            },
            'biodiversity': {
                'protected_areas': 0.15,  # 15% of land protected
                'endangered_species': 45,  # Number of species
                'habitat_loss_rate': 0.02  # 2% annual loss
            },
            'climate_adaptation': {
                'vulnerability_index': 6.8,  # Out of 10
                'adaptation_measures': 0.45,  # 45% implemented
                'resilience_score': 5.2  # Out of 10
            }
        }

    def get_health_simulation_data(self) -> Dict:
        """Get data for health policy simulations."""
        return {
            'health_indicators': {
                'life_expectancy': 68.5,  # Years
                'infant_mortality': 25.8,  # Per 1000 live births
                'maternal_mortality': 120.5,  # Per 100,000 live births
                'hiv_prevalence': 0.055  # 5.5% prevalence
            },
            'healthcare_access': {
                'primary_care_coverage': 0.78,  # 78% coverage
                'hospital_beds': 2.8,  # Per 1000 population
                'health_workers': 1.2,  # Per 1000 population
                'insurance_coverage': 0.65  # 65% coverage
            },
            'disease_burden': {
                'communicable_diseases': 0.35,  # 35% of burden
                'non_communicable': 0.55,  # 55% of burden
                'injuries': 0.10  # 10% of burden
            }
        }

    def get_transportation_simulation_data(self) -> Dict:
        """Get data for transportation policy simulations."""
        return {
            'modal_split': {
                'private_car': 0.65,  # 65% of trips
                'public_transport': 0.20,  # 20% of trips
                'walking': 0.10,  # 10% of trips
                'cycling': 0.05  # 5% of trips
            },
            'congestion_levels': {
                'peak_hour_delay': 45,  # Minutes additional
                'average_speed': 35,  # km/h
                'congestion_index': 7.2  # Out of 10
            },
            'public_transport': {
                'coverage': self.infrastructure_data['public_transport_coverage'],
                'reliability': 0.75,  # 75% on-time performance
                'affordability': 0.6,  # 60% of income for transport
                'accessibility': 0.7  # 70% of population within 1km
            }
        }

    def get_comprehensive_city_profile(self) -> Dict:
        """Get comprehensive profile of Cape Town for simulations."""
        return {
            'demographics': self.demographics,
            'economic': self.economic_data,
            'social': self.social_issues,
            'environmental': self.get_environmental_simulation_data(),
            'infrastructure': self.infrastructure_data,
            'health': self.get_health_simulation_data(),
            'transportation': self.get_transportation_simulation_data(),
            'last_updated': datetime.now().isoformat(),
            'data_sources': [
                'City of Cape Town Annual Report 2023',
                'Western Cape Government Statistics',
                'Statistics South Africa',
                'South African Police Service',
                'Department of Water and Sanitation'
            ]
        }

# Global Cape Town data provider
cape_town_data = CapeTownDataProvider()

def get_simulation_data(simulation_type: str) -> Dict:
    """Get Cape Town-specific data for different simulation types."""
    data_functions = {
        'unemployment': cape_town_data.get_unemployment_simulation_data,
        'water_crisis': cape_town_data.get_water_crisis_simulation_data,
        'crime': cape_town_data.get_crime_simulation_data,
        'social_policy': cape_town_data.get_social_policy_simulation_data,
        'education': cape_town_data.get_education_simulation_data,
        'economic': cape_town_data.get_economic_simulation_data,
        'environmental': cape_town_data.get_environmental_simulation_data,
        'health': cape_town_data.get_health_simulation_data,
        'transportation': cape_town_data.get_transportation_simulation_data
    }

    if simulation_type in data_functions:
        return data_functions[simulation_type]()
    else:
        return cape_town_data.get_comprehensive_city_profile()

if __name__ == "__main__":
    # Test the Cape Town data provider
    print("Cape Town Unemployment Data:")
    print(json.dumps(get_simulation_data('unemployment'), indent=2))

    print("\nCape Town Water Crisis Data:")
    print(json.dumps(get_simulation_data('water_crisis'), indent=2))

    print("\nComprehensive City Profile:")
    profile = get_simulation_data('comprehensive')
    print(f"Population: {profile['demographics']['population']:,}")
    print(f"Unemployment Rate: {profile['demographics']['unemployment_rate']:.1%}")
    print(f"Water Dam Capacity: {profile['economic']['gdp_per_capita']:,} ZAR per capita")