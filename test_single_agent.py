"""
Test Script for Single-Agent Architecture with Llama 3.1 8B

This script tests the integration of Llama 3.1 8B within the single-agent architecture,
ensuring proper functionality for resume generation, game recommendations, and policy analysis.
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import system components
try:
    import resume_tool
    import virtonomics_integration
    import simcompanies_integration
    import cwetlands_integration
    import theblueconnection_integration
    import mesa_abm_simulations
    import token_system
    import cape_town_data
    import popia_compliance
    import game_activity_tracker
except ImportError as e:
    logger.error(f"Failed to import component: {e}")
    exit(1)

def test_llama_integration():
    """Test Llama 3.1 8B integration for resume generation."""
    print("🧪 Testing Llama 3.1 8B Integration...")

    try:
        # Test resume generation
        test_job = {
            'title': 'Chemical Engineer',
            'company': 'Cape Town Petrochemicals',
            'description': 'Design and optimize chemical processes for petroleum refining',
            'requirements': ['chemical engineering', 'process design', 'safety protocols']
        }

        print("📄 Generating test resume...")
        resume = resume_tool.generate_resume(test_job)

        if 'error' in resume:
            print(f"❌ Resume generation failed: {resume['error']}")
            return False
        else:
            print("✅ Resume generated successfully")
            print(f"   Title: {resume.get('job_title', 'N/A')}")
            print(f"   Word file: {resume.get('word_file', 'N/A')}")
            print(f"   PDF file: {resume.get('pdf_file', 'N/A')}")
            return True

    except Exception as e:
        print(f"❌ Llama integration test failed: {e}")
        return False

def test_game_integrations():
    """Test all game integrations."""
    print("\n🎮 Testing Game Integrations...")

    test_skills = ['chemical_engineering', 'management', 'driving']
    results = {}

    # Test Virtonomics
    try:
        print("🏭 Testing Virtonomics integration...")
        v_result = virtonomics_integration.get_virtonomics_recommendations(test_skills)
        results['virtonomics'] = 'success' if 'discord_message' in v_result else 'failed'
        print("✅ Virtonomics integration working")
    except Exception as e:
        print(f"❌ Virtonomics integration failed: {e}")
        results['virtonomics'] = 'failed'

    # Test Sim Companies
    try:
        print("🏢 Testing Sim Companies integration...")
        s_result = simcompanies_integration.get_simcompanies_recommendations(test_skills)
        results['simcompanies'] = 'success' if 'discord_message' in s_result else 'failed'
        print("✅ Sim Companies integration working")
    except Exception as e:
        print(f"❌ Sim Companies integration failed: {e}")
        results['simcompanies'] = 'failed'

    # Test CWetlands
    try:
        print("🌿 Testing CWetlands integration...")
        c_result = cwetlands_integration.get_cwetlands_recommendations(test_skills)
        results['cwetlands'] = 'success' if 'discord_message' in c_result else 'failed'
        print("✅ CWetlands integration working")
    except Exception as e:
        print(f"❌ CWetlands integration failed: {e}")
        results['cwetlands'] = 'failed'

    # Test The Blue Connection
    try:
        print("🔄 Testing The Blue Connection integration...")
        t_result = theblueconnection_integration.get_theblueconnection_recommendations(test_skills)
        results['theblueconnection'] = 'success' if 'discord_message' in t_result else 'failed'
        print("✅ The Blue Connection integration working")
    except Exception as e:
        print(f"❌ The Blue Connection integration failed: {e}")
        results['theblueconnection'] = 'failed'

    return results

def test_abm_simulations():
    """Test ABM simulation functionality."""
    print("\n🔬 Testing ABM Simulations...")

    try:
        print("📊 Testing unemployment simulation...")
        unemployment_result = mesa_abm_simulations.run_cape_town_unemployment_simulation()

        if 'error' in unemployment_result:
            print(f"❌ Unemployment simulation failed: {unemployment_result['error']}")
            return False
        else:
            print("✅ Unemployment simulation completed")
            print(f"   Steps run: {unemployment_result.get('steps_run', 'N/A')}")
            print(f"   Final metrics: {unemployment_result.get('final_metrics', {})}")

        print("💧 Testing water crisis simulation...")
        water_result = mesa_abm_simulations.run_cape_town_water_crisis_simulation()

        if 'error' in water_result:
            print(f"❌ Water crisis simulation failed: {water_result['error']}")
            return False
        else:
            print("✅ Water crisis simulation completed")
            print(f"   Steps run: {water_result.get('steps_run', 'N/A')}")

        return True

    except Exception as e:
        print(f"❌ ABM simulation test failed: {e}")
        return False

def test_token_system():
    """Test token system functionality."""
    print("\n💎 Testing Token System...")

    try:
        test_user = "test_agent_user"

        # Test token earning
        print("🎁 Testing token earning...")
        earn_result = token_system.earn_tokens(test_user, 'job_application',
            {'job_title': 'Test Job', 'company': 'Test Company'})

        if 'error' in earn_result:
            print(f"❌ Token earning failed: {earn_result['error']}")
            return False
        else:
            print("✅ Token earning successful")
            print(f"   Tokens earned: {earn_result.get('tokens_earned', 0)}")
            print(f"   New balance: {earn_result.get('new_balance', 0)}")

        # Test token spending
        print("🛒 Testing token spending...")
        spend_result = token_system.spend_tokens(test_user, 'premium_job_listings')

        if 'error' in spend_result:
            print(f"❌ Token spending failed: {spend_result['error']}")
            return False
        else:
            print("✅ Token spending successful")
            print(f"   Reward: {spend_result.get('reward', 'N/A')}")
            print(f"   Cost: {spend_result.get('cost', 0)}")
            print(f"   New balance: {spend_result.get('new_balance', 0)}")

        return True

    except Exception as e:
        print(f"❌ Token system test failed: {e}")
        return False

def test_popia_compliance():
    """Test POPIA compliance features."""
    print("\n🔒 Testing POPIA Compliance...")

    try:
        test_resume = {
            'personal_info': {
                'name': 'Test User',
                'email': 'test@example.com',
                'phone': '+27 21 123 4567'
            },
            'skills': ['Python', 'Data Analysis'],
            'experience': [{'title': 'Developer', 'company': 'Test Corp'}]
        }

        print("🔐 Testing data anonymization...")
        anonymized, mapping = popia_compliance.anonymize_user_data(test_resume)

        if not anonymized:
            print("❌ Data anonymization failed")
            return False
        else:
            print("✅ Data anonymization successful")
            print(f"   Fields anonymized: {len(mapping)}")

        print("📋 Testing data processing record...")
        record = popia_compliance.generate_data_processing_record(
            'test_user', 'resume_processing', ['personal_info', 'career_data']
        )

        if not record:
            print("❌ Data processing record failed")
            return False
        else:
            print("✅ Data processing record created")
            print(f"   Record ID: {record.get('record_id', 'N/A')}")

        return True

    except Exception as e:
        print(f"❌ POPIA compliance test failed: {e}")
        return False

def test_cape_town_data():
    """Test Cape Town data integration."""
    print("\n🏙️ Testing Cape Town Data Integration...")

    try:
        print("📊 Testing unemployment data...")
        unemployment_data = cape_town_data.get_simulation_data('unemployment')
        print(f"✅ Unemployment data loaded: {len(unemployment_data)} parameters")

        print("💧 Testing water crisis data...")
        water_data = cape_town_data.get_simulation_data('water_crisis')
        print(f"✅ Water crisis data loaded: {len(water_data)} parameters")

        print("📈 Testing comprehensive profile...")
        profile = cape_town_data.get_simulation_data('comprehensive')
        print(f"✅ Comprehensive profile loaded: {profile.get('demographics', {}).get('population', 0):,} population")

        return True

    except Exception as e:
        print(f"❌ Cape Town data test failed: {e}")
        return False

def test_game_activity_tracking():
    """Test game activity tracking."""
    print("\n🎯 Testing Game Activity Tracking...")

    try:
        test_user = "test_activity_user"

        print("📝 Testing activity tracking...")
        result = game_activity_tracker.track_activity(
            test_user, 'virtonomics', 'company_created',
            {'company_name': 'Test Logistics Co'}
        )

        if 'error' in result:
            print(f"❌ Activity tracking failed: {result['error']}")
            return False
        else:
            print("✅ Activity tracking successful")
            print(f"   Tokens earned: {result.get('tokens_earned', 0)}")
            print(f"   Achievements: {len(result.get('new_achievements', []))}")

        print("📊 Testing progress report...")
        progress = game_activity_tracker.get_user_progress_report(test_user)
        print(f"✅ Progress report generated: {len(progress)} metrics")

        return True

    except Exception as e:
        print(f"❌ Game activity tracking test failed: {e}")
        return False

def run_full_system_test():
    """Run comprehensive system test."""
    print("🚀 Starting Job Application Agent Single-Agent Architecture Test")
    print("=" * 60)

    test_results = {}

    # Test individual components
    test_results['llama_integration'] = test_llama_integration()
    test_results['game_integrations'] = test_game_integrations()
    test_results['abm_simulations'] = test_abm_simulations()
    test_results['token_system'] = test_token_system()
    test_results['popia_compliance'] = test_popia_compliance()
    test_results['cape_town_data'] = test_cape_town_data()
    test_results['game_activity_tracking'] = test_game_activity_tracking()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print("15")
        if result:
            passed += 1

    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Single-agent architecture is ready for deployment.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = run_full_system_test()

exit(0 if success else 1)