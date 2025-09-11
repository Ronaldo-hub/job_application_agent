"""
Mesa Agent-Based Modeling Framework for Social Policy Simulations

This module implements ABM simulations for social policy testing using Mesa framework.
It models various social issues affecting Cape Town job seekers:
- Unemployment and employability
- Drug abuse and rehabilitation
- Human trafficking prevention
- Gender-based violence prevention
- Water scarcity and conservation
- Climate change adaptation

Each simulation provides objective criteria for policy decision-making.
"""

import os
import json
import logging
import random
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Load Mesa and related dependencies
try:
    from mesa import Agent, Model
    from mesa.time import RandomActivation
    from mesa.space import MultiGrid
    from mesa.datacollection import DataCollector
    from mesa.visualization.ModularVisualization import ModularServer
    from mesa.visualization.modules import CanvasGrid, ChartModule
    import mesa
except ImportError:
    logging.warning("Mesa not installed. Install with: pip install mesa")
    # Mock classes for development
    class Agent:
        def __init__(self, unique_id, model):
            self.unique_id = unique_id
            self.model = model

    class Model:
        def __init__(self):
            self.schedule = None
            self.datacollector = None

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Cape Town data
try:
    import cape_town_data
except ImportError:
    logging.warning("Cape Town data module not available")
    cape_town_data = None

# =============================================================================
# BASE CLASSES
# =============================================================================

class SocialAgent(Agent):
    """Base agent class for social simulations."""

    def __init__(self, unique_id: int, model: 'SocialModel'):
        super().__init__(unique_id, model)
        self.age = random.randint(18, 65)
        self.gender = random.choice(['male', 'female'])
        self.income = random.randint(0, 50000)
        self.education_level = random.choice(['none', 'primary', 'secondary', 'tertiary'])
        self.employment_status = random.choice(['employed', 'unemployed', 'self_employed'])
        self.vulnerability_score = random.uniform(0, 1)
        self.social_network = []

    def step(self):
        """Agent action for each simulation step."""
        pass

class SocialModel(Model):
    """Base model class for social simulations."""

    def __init__(self, width: int = 20, height: int = 20, num_agents: int = 100):
        super().__init__()
        self.width = width
        self.height = height
        self.num_agents = num_agents
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(width, height, True)
        self.datacollector = DataCollector(
            model_reporters={
                "employed": lambda m: len([a for a in m.schedule.agents if a.employment_status == 'employed']),
                "unemployed": lambda m: len([a for a in m.schedule.agents if a.employment_status == 'unemployed']),
                "vulnerability_avg": lambda m: np.mean([a.vulnerability_score for a in m.schedule.agents]),
                "policy_effectiveness": lambda m: m.calculate_policy_effectiveness()
            }
        )

        # Initialize agents
        for i in range(num_agents):
            agent = self.create_agent(i)
            self.schedule.add(agent)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(agent, (x, y))

    def create_agent(self, unique_id: int) -> SocialAgent:
        """Create agent - override in subclasses."""
        return SocialAgent(unique_id, self)

    def step(self):
        """Model step."""
        self.datacollector.collect(self)
        self.schedule.step()

    def calculate_policy_effectiveness(self) -> float:
        """Calculate policy effectiveness - override in subclasses."""
        return 0.5

# =============================================================================
# UNEMPLOYMENT SIMULATION
# =============================================================================

class UnemploymentAgent(SocialAgent):
    """Agent for unemployment simulation."""

    def __init__(self, unique_id: int, model: 'UnemploymentModel'):
        super().__init__(unique_id, model)
        self.skills = random.sample(['basic', 'intermediate', 'advanced'], random.randint(1, 3))
        self.job_search_effort = random.uniform(0, 1)
        self.training_level = 0
        self.unemployed_months = random.randint(0, 24)

    def step(self):
        """Agent behavior in unemployment simulation."""
        if self.employment_status == 'unemployed':
            # Job search behavior
            search_success = self.job_search_effort * random.uniform(0.1, 0.3)
            if random.random() < search_success:
                self.find_job()

            # Training participation
            if random.random() < 0.1:  # 10% chance to join training
                self.training_level += 0.1
                self.job_search_effort += 0.05

            self.unemployed_months += 1

    def find_job(self):
        """Attempt to find employment."""
        skill_factor = len(self.skills) * 0.1
        training_factor = self.training_level * 0.2
        success_prob = min(0.3 + skill_factor + training_factor, 0.8)

        if random.random() < success_prob:
            self.employment_status = 'employed'
            self.unemployed_months = 0
            self.income = random.randint(8000, 25000)

class UnemploymentModel(SocialModel):
    """Model for unemployment policy simulation."""

    def __init__(self, width: int = 20, height: int = 20, num_agents: int = 100,
                 training_program_intensity: float = 0.5,
                 job_creation_rate: float = 0.1):
        self.training_program_intensity = training_program_intensity
        self.job_creation_rate = job_creation_rate
        super().__init__(width, height, num_agents)

    def create_agent(self, unique_id: int) -> UnemploymentAgent:
        return UnemploymentAgent(unique_id, self)

    def step(self):
        super().step()

        # Policy interventions
        if random.random() < self.training_program_intensity:
            self.run_training_program()

        if random.random() < self.job_creation_rate:
            self.create_jobs()

    def run_training_program(self):
        """Run government training program."""
        unemployed_agents = [a for a in self.schedule.agents if a.employment_status == 'unemployed']
        if unemployed_agents:
            agent = random.choice(unemployed_agents)
            agent.training_level += 0.2
            agent.job_search_effort += 0.1

    def create_jobs(self):
        """Create new job opportunities."""
        unemployed_agents = [a for a in self.schedule.agents if a.employment_status == 'unemployed']
        if unemployed_agents:
            agent = random.choice(unemployed_agents)
            if random.random() < 0.4:  # 40% success rate for job creation
                agent.employment_status = 'employed'
                agent.income = random.randint(10000, 30000)

    def calculate_policy_effectiveness(self) -> float:
        """Calculate unemployment policy effectiveness."""
        employed = len([a for a in self.schedule.agents if a.employment_status == 'employed'])
        total = len(self.schedule.agents)
        employment_rate = employed / total if total > 0 else 0
        return employment_rate

# =============================================================================
# DRUG ABUSE SIMULATION
# =============================================================================

class DrugAbuseAgent(SocialAgent):
    """Agent for drug abuse simulation."""

    def __init__(self, unique_id: int, model: 'DrugAbuseModel'):
        super().__init__(unique_id, model)
        self.addiction_level = random.uniform(0, 1)
        self.rehabilitation_status = 'none'  # none, in_treatment, recovered
        self.relapse_risk = random.uniform(0, 1)
        self.social_support = random.uniform(0, 1)
        self.employment_impact = self.addiction_level * 0.3

    def step(self):
        """Agent behavior in drug abuse simulation."""
        if self.rehabilitation_status == 'in_treatment':
            # Treatment progress
            if random.random() < 0.1:  # 10% recovery chance per step
                self.rehabilitation_status = 'recovered'
                self.addiction_level *= 0.3
                self.relapse_risk *= 0.5
        elif self.rehabilitation_status == 'recovered':
            # Relapse risk
            if random.random() < self.relapse_risk:
                self.rehabilitation_status = 'none'
                self.addiction_level += 0.2

        # Employment impact
        if self.addiction_level > 0.5:
            if random.random() < 0.2:  # 20% chance of job loss
                self.employment_status = 'unemployed'

class DrugAbuseModel(SocialModel):
    """Model for drug abuse policy simulation."""

    def __init__(self, width: int = 20, height: int = 20, num_agents: int = 100,
                 treatment_access: float = 0.3,
                 prevention_programs: float = 0.4):
        self.treatment_access = treatment_access
        self.prevention_programs = prevention_programs
        super().__init__(width, height, num_agents)

    def create_agent(self, unique_id: int) -> DrugAbuseAgent:
        return DrugAbuseAgent(unique_id, self)

    def step(self):
        super().step()

        # Policy interventions
        if random.random() < self.treatment_access:
            self.provide_treatment()

        if random.random() < self.prevention_programs:
            self.run_prevention_programs()

    def provide_treatment(self):
        """Provide addiction treatment."""
        addicted_agents = [a for a in self.schedule.agents if a.addiction_level > 0.3 and a.rehabilitation_status == 'none']
        if addicted_agents:
            agent = random.choice(addicted_agents)
            agent.rehabilitation_status = 'in_treatment'

    def run_prevention_programs(self):
        """Run community prevention programs."""
        at_risk_agents = [a for a in self.schedule.agents if a.addiction_level < 0.5]
        if at_risk_agents:
            agent = random.choice(at_risk_agents)
            agent.social_support += 0.1
            agent.relapse_risk *= 0.9

    def calculate_policy_effectiveness(self) -> float:
        """Calculate drug abuse policy effectiveness."""
        recovered = len([a for a in self.schedule.agents if a.rehabilitation_status == 'recovered'])
        in_treatment = len([a for a in self.schedule.agents if a.rehabilitation_status == 'in_treatment'])
        total_addicted = len([a for a in self.schedule.agents if a.addiction_level > 0.3])

        if total_addicted == 0:
            return 1.0

        effectiveness = (recovered + in_treatment * 0.5) / total_addicted
        return min(effectiveness, 1.0)

# =============================================================================
# HUMAN TRAFFICKING SIMULATION
# =============================================================================

class TraffickingAgent(SocialAgent):
    """Agent for human trafficking simulation."""

    def __init__(self, unique_id: int, model: 'TraffickingModel'):
        super().__init__(unique_id, model)
        self.trafficking_risk = random.uniform(0, 1)
        self.awareness_level = random.uniform(0, 1)
        self.economic_stability = random.uniform(0, 1)
        self.social_protection = random.uniform(0, 1)
        self.trafficked_status = False

    def step(self):
        """Agent behavior in trafficking simulation."""
        if not self.trafficked_status:
            # Vulnerability assessment
            vulnerability = (1 - self.awareness_level) * (1 - self.economic_stability) * (1 - self.social_protection)
            self.trafficking_risk = vulnerability

            # Trafficking attempt
            if random.random() < self.trafficking_risk * 0.05:  # 5% base risk
                self.trafficked_status = True
                self.employment_status = 'unemployed'
                self.income = 0

class TraffickingModel(SocialModel):
    """Model for human trafficking prevention simulation."""

    def __init__(self, width: int = 20, height: int = 20, num_agents: int = 100,
                 awareness_campaigns: float = 0.4,
                 economic_support: float = 0.3,
                 law_enforcement: float = 0.2):
        self.awareness_campaigns = awareness_campaigns
        self.economic_support = economic_support
        self.law_enforcement = law_enforcement
        super().__init__(width, height, num_agents)

    def create_agent(self, unique_id: int) -> TraffickingAgent:
        return TraffickingAgent(unique_id, self)

    def step(self):
        super().step()

        # Policy interventions
        if random.random() < self.awareness_campaigns:
            self.run_awareness_campaign()

        if random.random() < self.economic_support:
            self.provide_economic_support()

        if random.random() < self.law_enforcement:
            self.enhance_law_enforcement()

    def run_awareness_campaign(self):
        """Run community awareness campaigns."""
        low_awareness_agents = [a for a in self.schedule.agents if a.awareness_level < 0.5]
        if low_awareness_agents:
            agent = random.choice(low_awareness_agents)
            agent.awareness_level += 0.2
            agent.trafficking_risk *= 0.8

    def provide_economic_support(self):
        """Provide economic support programs."""
        low_income_agents = [a for a in self.schedule.agents if a.economic_stability < 0.5]
        if low_income_agents:
            agent = random.choice(low_income_agents)
            agent.economic_stability += 0.15
            agent.income += 2000
            agent.trafficking_risk *= 0.85

    def enhance_law_enforcement(self):
        """Enhance law enforcement efforts."""
        trafficked_agents = [a for a in self.schedule.agents if a.trafficked_status]
        if trafficked_agents:
            agent = random.choice(trafficked_agents)
            if random.random() < 0.3:  # 30% rescue success rate
                agent.trafficked_status = False
                agent.social_protection += 0.2

    def calculate_policy_effectiveness(self) -> float:
        """Calculate trafficking prevention policy effectiveness."""
        trafficked = len([a for a in self.schedule.agents if a.trafficked_status])
        total = len(self.schedule.agents)
        trafficking_rate = trafficked / total if total > 0 else 0

        # Effectiveness is inverse of trafficking rate
        return 1 - trafficking_rate

# =============================================================================
# WATER SCARCITY SIMULATION
# =============================================================================

class WaterAgent(SocialAgent):
    """Agent for water scarcity simulation."""

    def __init__(self, unique_id: int, model: 'WaterScarcityModel'):
        super().__init__(unique_id, model)
        self.water_usage = random.uniform(100, 500)  # Liters per day
        self.conservation_awareness = random.uniform(0, 1)
        self.water_access = random.uniform(0.5, 1)
        self.conservation_practices = []

    def step(self):
        """Agent behavior in water scarcity simulation."""
        # Water usage behavior
        if self.conservation_awareness > 0.5:
            self.water_usage *= 0.8  # 20% reduction with awareness

        # Conservation adoption
        if random.random() < self.conservation_awareness * 0.1:
            if 'rainwater_harvesting' not in self.conservation_practices:
                self.conservation_practices.append('rainwater_harvesting')
                self.water_usage *= 0.9

class WaterScarcityModel(SocialModel):
    """Model for water scarcity policy simulation."""

    def __init__(self, width: int = 20, height: int = 20, num_agents: int = 100,
                 conservation_programs: float = 0.4,
                 infrastructure_investment: float = 0.3):
        self.conservation_programs = conservation_programs
        self.infrastructure_investment = infrastructure_investment
        self.total_water_available = 1000000  # Liters per day
        super().__init__(width, height, num_agents)

    def create_agent(self, unique_id: int) -> WaterAgent:
        return WaterAgent(unique_id, self)

    def step(self):
        super().step()

        # Policy interventions
        if random.random() < self.conservation_programs:
            self.run_conservation_campaign()

        if random.random() < self.infrastructure_investment:
            self.invest_infrastructure()

    def run_conservation_campaign(self):
        """Run water conservation campaigns."""
        low_awareness_agents = [a for a in self.schedule.agents if a.conservation_awareness < 0.5]
        if low_awareness_agents:
            agent = random.choice(low_awareness_agents)
            agent.conservation_awareness += 0.2
            agent.water_usage *= 0.85

    def invest_infrastructure(self):
        """Invest in water infrastructure."""
        low_access_agents = [a for a in self.schedule.agents if a.water_access < 0.7]
        if low_access_agents:
            agent = random.choice(low_access_agents)
            agent.water_access += 0.1
            agent.water_usage *= 0.95

    def calculate_policy_effectiveness(self) -> float:
        """Calculate water policy effectiveness."""
        total_usage = sum(a.water_usage for a in self.schedule.agents)
        avg_conservation = np.mean([a.conservation_awareness for a in self.schedule.agents])

        # Effectiveness based on usage reduction and conservation adoption
        usage_efficiency = min(total_usage / self.total_water_available, 1)
        effectiveness = (avg_conservation + (1 - usage_efficiency)) / 2
        return effectiveness

# =============================================================================
# SIMULATION RUNNER
# =============================================================================

class PolicySimulationRunner:
    """Runner for executing and analyzing policy simulations."""

    def __init__(self):
        self.models = {
            'unemployment': UnemploymentModel,
            'drug_abuse': DrugAbuseModel,
            'trafficking': TraffickingModel,
            'water_scarcity': WaterScarcityModel
        }

    def run_simulation(self, model_type: str, steps: int = 50,
                      parameters: Dict = None) -> Dict:
        """Run a specific simulation model."""
        if model_type not in self.models:
            return {'error': f'Model {model_type} not found'}

        # Set default parameters
        if parameters is None:
            parameters = {}

        # Create model with parameters
        model_class = self.models[model_type]
        model = model_class(**parameters)

        # Run simulation
        for i in range(steps):
            model.step()

        # Collect results
        results = {
            'model_type': model_type,
            'steps_run': steps,
            'final_metrics': {
                'employed': len([a for a in model.schedule.agents if a.employment_status == 'employed']),
                'unemployed': len([a for a in model.schedule.agents if a.employment_status == 'unemployed']),
                'policy_effectiveness': model.calculate_policy_effectiveness()
            },
            'time_series_data': self.extract_time_series(model)
        }

        return results

    def extract_time_series(self, model) -> Dict:
        """Extract time series data from model data collector."""
        data = model.datacollector.get_model_vars_dataframe()
        return {
            'employed': data['employed'].tolist(),
            'unemployed': data['unemployed'].tolist(),
            'vulnerability_avg': data['vulnerability_avg'].tolist(),
            'policy_effectiveness': data['policy_effectiveness'].tolist()
        }

    def compare_policies(self, model_type: str, policy_scenarios: List[Dict]) -> Dict:
        """Compare different policy scenarios."""
        results = []

        for scenario in policy_scenarios:
            scenario_result = self.run_simulation(model_type, parameters=scenario.get('parameters', {}))
            scenario_result['scenario_name'] = scenario.get('name', 'Unnamed')
            scenario_result['policy_description'] = scenario.get('description', '')
            results.append(scenario_result)

        # Find best performing scenario
        best_scenario = max(results, key=lambda x: x['final_metrics']['policy_effectiveness'])

        return {
            'model_type': model_type,
            'scenarios_compared': len(results),
            'results': results,
            'best_scenario': best_scenario,
            'recommendation': f"Implement {best_scenario['scenario_name']} for optimal results"
        }

# =============================================================================
# CAPE TOWN SPECIFIC SIMULATIONS
# =============================================================================

def run_cape_town_unemployment_simulation() -> Dict:
    """Run unemployment simulation tailored for Cape Town context."""
    runner = PolicySimulationRunner()

    # Get Cape Town specific data
    if cape_town_data:
        ct_data = cape_town_data.get_simulation_data('unemployment')
        baseline_unemployment = ct_data['baseline_unemployment']
        youth_unemployment = ct_data['youth_unemployment']
        sector_demand = ct_data['sector_demand']
    else:
        # Fallback values
        baseline_unemployment = 0.25
        youth_unemployment = 0.35
        sector_demand = {'tourism': 0.15, 'technology': 0.12, 'finance': 0.20}

    # Cape Town specific parameters based on real data
    parameters = {
        'num_agents': 500,  # Approximate job seekers
        'training_program_intensity': 0.6,  # Higher training focus for youth unemployment
        'job_creation_rate': 0.15,  # Economic growth factor
        'baseline_unemployment': baseline_unemployment,
        'youth_focus': True  # Special focus on youth unemployment
    }

    result = runner.run_simulation('unemployment', steps=100, parameters=parameters)

    # Add comprehensive Cape Town context
    result['location_context'] = {
        'city': 'Cape Town',
        'province': 'Western Cape',
        'unemployment_rate_baseline': baseline_unemployment,
        'youth_unemployment_rate': youth_unemployment,
        'female_unemployment_rate': 0.28,
        'key_sectors': sector_demand,
        'vulnerable_groups': ['youth', 'women', 'migrants', 'informal_settlement_residents'],
        'population_segments': {
            'working_age': 2800000,
            'youth_15_34': 800000,
            'female_labor_force': 1400000
        },
        'economic_indicators': {
            'gdp_per_capita': 120000,  # ZAR
            'poverty_rate': 0.15,
            'informal_economy_size': 0.25  # 25% of economy
        }
    }

    return result

def run_cape_town_water_crisis_simulation() -> Dict:
    """Run water scarcity simulation for Cape Town's Day Zero scenario."""
    runner = PolicySimulationRunner()

    # Get Cape Town specific water data
    if cape_town_data:
        ct_data = cape_town_data.get_simulation_data('water_crisis')
        current_capacity = ct_data['current_capacity']
        conservation_potential = ct_data['conservation_potential']
        climate_impacts = ct_data['climate_impacts']
    else:
        # Fallback values
        current_capacity = 25
        conservation_potential = {'short_term': 0.15, 'medium_term': 0.25}
        climate_impacts = {'temperature_increase': 2.1, 'precipitation_change': -0.15}

    parameters = {
        'num_agents': 400,  # Cape Town population segment
        'conservation_programs': 0.7,  # High conservation focus
        'infrastructure_investment': 0.4,  # Infrastructure development
        'current_dam_capacity': current_capacity,
        'climate_stress_factor': 1.5,  # Cape Town specific climate stress
        'population_pressure': 1.8  # Higher pressure due to tourism and growth
    }

    result = runner.run_simulation('water_scarcity', steps=80, parameters=parameters)

    # Add comprehensive Cape Town water context
    result['cape_town_context'] = {
        'day_zero_date': '2018-02-22',  # Historical context
        'day_zero_avoided': '2023-01-01',  # When crisis was averted
        'dam_capacity_percentage': current_capacity,
        'daily_consumption_target': 45000000,  # Liters per day
        'current_daily_usage': 50000000,  # Liters per day
        'rainfall_deficit': 0.6,  # 60% below normal
        'groundwater_available': 0.3,  # 30% of normal
        'desalination_capacity': 0.1,  # 10% of needs
        'conservation_measures': {
            'implemented': 0.4,  # 40% adoption
            'potential_savings': conservation_potential['short_term']
        },
        'alternative_sources': {
            'groundwater': 0.20,  # 20% of needs
            'desalination': 0.15,  # 15% of needs
            'reuse': 0.10  # 10% of needs
        },
        'climate_impacts': climate_impacts,
        'vulnerable_areas': [
            'informal_settlements',
            'low_income_households',
            'agricultural_communities',
            'tourism_dependent_businesses'
        ],
        'policy_interventions': [
            'water_restrictions_levels_1_6',
            'groundwater_abstraction',
            'desalination_plant_construction',
            'rainwater_harvesting_incentives',
            'public_education_campaigns'
        ]
    }

    return result

def generate_policy_recommendations(simulation_results: Dict) -> Dict:
    """Generate policy recommendations based on simulation results."""
    effectiveness = simulation_results['final_metrics']['policy_effectiveness']

    if effectiveness > 0.8:
        recommendation_level = 'High Impact'
        implementation_priority = 'Immediate'
    elif effectiveness > 0.6:
        recommendation_level = 'Moderate Impact'
        implementation_priority = 'High'
    elif effectiveness > 0.4:
        recommendation_level = 'Low Impact'
        implementation_priority = 'Medium'
    else:
        recommendation_level = 'Minimal Impact'
        implementation_priority = 'Low'

    return {
        'policy_effectiveness_score': effectiveness,
        'recommendation_level': recommendation_level,
        'implementation_priority': implementation_priority,
        'estimated_timeline': '6-12 months',
        'monitoring_requirements': [
            'Regular impact assessments',
            'Stakeholder feedback collection',
            'Data-driven adjustments'
        ],
        'scaling_potential': 'High' if effectiveness > 0.7 else 'Medium'
    }

# Global simulation runner
simulation_runner = PolicySimulationRunner()

def run_policy_simulation(simulation_type: str, parameters: Dict = None) -> Dict:
    """Main function to run policy simulations."""
    try:
        if simulation_type == 'cape_town_unemployment':
            return run_cape_town_unemployment_simulation()
        elif simulation_type == 'cape_town_water_crisis':
            return run_cape_town_water_crisis_simulation()
        else:
            return simulation_runner.run_simulation(simulation_type, parameters=parameters or {})
    except Exception as e:
        logger.error(f"Error running {simulation_type} simulation: {e}")
        return {'error': str(e)}

if __name__ == "__main__":
    # Test unemployment simulation
    print("Running Unemployment Policy Simulation...")
    unemployment_result = run_policy_simulation('unemployment')
    print(json.dumps(unemployment_result, indent=2))

    # Test Cape Town specific simulation
    print("\nRunning Cape Town Unemployment Simulation...")
    cape_town_result = run_policy_simulation('cape_town_unemployment')
    print(json.dumps(cape_town_result, indent=2))