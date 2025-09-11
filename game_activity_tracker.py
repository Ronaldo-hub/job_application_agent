"""
Game Activity Tracking and Progress Notifications Module

This module tracks user progress in serious games and provides notifications
about achievements, milestones, and personalized recommendations.

Features:
- Activity logging and progress tracking
- Achievement system with milestones
- Progress notifications via Discord
- Personalized recommendations based on performance
- Integration with token system for rewards
- Cape Town-specific context and goals
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import dependencies
try:
    import virtonomics_integration
    import simcompanies_integration
    import cwetlands_integration
    import theblueconnection_integration
    import token_system
    import cape_town_data
except ImportError as e:
    logging.warning(f"Dependency not available: {e}")

class GameActivityTracker:
    """Tracks user progress and activities in serious games."""

    def __init__(self):
        self.game_modules = {
            'virtonomics': virtonomics_integration,
            'simcompanies': simcompanies_integration,
            'cwetlands': cwetlands_integration,
            'theblueconnection': theblueconnection_integration
        }

        # Achievement definitions
        self.achievements = {
            'first_login': {
                'name': 'First Steps',
                'description': 'Logged into your first serious game',
                'icon': '🎮',
                'tokens': 25,
                'category': 'engagement'
            },
            'week_warrior': {
                'name': 'Week Warrior',
                'description': 'Played games for 7 consecutive days',
                'icon': '⚔️',
                'tokens': 100,
                'category': 'consistency'
            },
            'skill_builder': {
                'name': 'Skill Builder',
                'description': 'Completed 10 skill-building activities',
                'icon': '🏗️',
                'tokens': 150,
                'category': 'learning'
            },
            'business_tycoon': {
                'name': 'Business Tycoon',
                'description': 'Achieved profitability in Sim Companies',
                'icon': '💰',
                'tokens': 200,
                'category': 'achievement'
            },
            'water_champion': {
                'name': 'Water Champion',
                'description': 'Successfully managed water resources in CWetlands',
                'icon': '💧',
                'tokens': 175,
                'category': 'sustainability'
            },
            'circular_innovator': {
                'name': 'Circular Innovator',
                'description': 'Implemented circular economy solutions',
                'icon': '🔄',
                'tokens': 180,
                'category': 'innovation'
            },
            'policy_expert': {
                'name': 'Policy Expert',
                'description': 'Influenced 5 policy simulations',
                'icon': '📊',
                'tokens': 250,
                'category': 'impact'
            },
            'community_leader': {
                'name': 'Community Leader',
                'description': 'Helped 10 other users with game activities',
                'icon': '👑',
                'tokens': 300,
                'category': 'leadership'
            }
        }

        # Milestone definitions
        self.milestones = {
            'activities_completed': [5, 10, 25, 50, 100],
            'games_explored': [1, 2, 3, 4],
            'skills_developed': [3, 5, 8, 12],
            'days_active': [7, 14, 30, 60, 90],
            'tokens_earned': [100, 500, 1000, 2500, 5000]
        }

        # Cape Town-specific goals
        self.cape_town_goals = {
            'water_conservation': {
                'target': 'Reduce virtual water usage by 25%',
                'reward_tokens': 150,
                'impact': 'Contributes to real water conservation awareness'
            },
            'job_creation': {
                'target': 'Create 50 virtual jobs in business simulations',
                'reward_tokens': 200,
                'impact': 'Develops entrepreneurship skills for real job creation'
            },
            'sustainable_business': {
                'target': 'Achieve circular economy certification in games',
                'reward_tokens': 175,
                'impact': 'Promotes sustainable business practices'
            },
            'community_impact': {
                'target': 'Participate in 10 community policy discussions',
                'reward_tokens': 125,
                'impact': 'Builds community engagement skills'
            }
        }

    def track_activity(self, user_id: str, game: str, activity_type: str,
                      details: Dict = None) -> Dict:
        """Track a game activity for a user."""
        try:
            activity_record = {
                'user_id': user_id,
                'game': game,
                'activity_type': activity_type,
                'timestamp': datetime.now(),
                'details': details or {},
                'session_id': f"{user_id}_{int(datetime.now().timestamp())}"
            }

            # Award tokens for the activity
            if hasattr(token_system, 'earn_tokens'):
                token_result = token_system.earn_tokens(user_id, 'game_activity_completion',
                    {'game': game, 'activity': activity_type})
                activity_record['tokens_earned'] = token_result.get('tokens_earned', 0)

            # Check for achievements
            new_achievements = self._check_achievements(user_id, activity_record)

            # Check for milestones
            new_milestones = self._check_milestones(user_id, activity_record)

            # Generate progress notification
            notification = self._generate_progress_notification(user_id, activity_record,
                                                              new_achievements, new_milestones)

            result = {
                'activity_recorded': True,
                'tokens_earned': activity_record.get('tokens_earned', 0),
                'new_achievements': new_achievements,
                'new_milestones': new_milestones,
                'notification': notification,
                'next_recommendations': self._get_personalized_recommendations(user_id)
            }

            logger.info(f"Activity tracked for user {user_id}: {game} - {activity_type}")
            return result

        except Exception as e:
            logger.error(f"Error tracking activity for user {user_id}: {e}")
            return {'error': str(e)}

    def _check_achievements(self, user_id: str, activity_record: Dict) -> List[Dict]:
        """Check if user has unlocked new achievements."""
        new_achievements = []

        try:
            # This would typically query user activity history
            # For now, simulate achievement checking based on activity type

            game = activity_record['game']
            activity_type = activity_record['activity_type']

            # Game-specific achievements
            if game == 'virtonomics' and activity_type == 'company_created':
                if 'first_login' not in self._get_user_achievements(user_id):
                    new_achievements.append(self.achievements['first_login'])

            elif game == 'simcompanies' and activity_type == 'profit_achieved':
                if 'business_tycoon' not in self._get_user_achievements(user_id):
                    new_achievements.append(self.achievements['business_tycoon'])

            elif game == 'cwetlands' and activity_type == 'water_goals_met':
                if 'water_champion' not in self._get_user_achievements(user_id):
                    new_achievements.append(self.achievements['water_champion'])

            elif game == 'theblueconnection' and activity_type == 'circular_solution':
                if 'circular_innovator' not in self._get_user_achievements(user_id):
                    new_achievements.append(self.achievements['circular_innovator'])

            # Award tokens for new achievements
            for achievement in new_achievements:
                if hasattr(token_system, 'earn_tokens'):
                    token_system.earn_tokens(user_id, 'milestone_achievement',
                        {'achievement': achievement['name']})

        except Exception as e:
            logger.error(f"Error checking achievements: {e}")

        return new_achievements

    def _check_milestones(self, user_id: str, activity_record: Dict) -> List[Dict]:
        """Check if user has reached new milestones."""
        new_milestones = []

        try:
            # Simulate milestone checking
            # In a real implementation, this would query user statistics

            milestones_reached = [
                {
                    'type': 'activities_completed',
                    'value': 5,
                    'reward_tokens': 50,
                    'description': 'Completed 5 game activities'
                }
            ]

            # Award tokens for milestones
            for milestone in milestones_reached:
                if hasattr(token_system, 'earn_tokens'):
                    token_system.earn_tokens(user_id, 'milestone_achievement',
                        {'milestone': milestone['description']})

            new_milestones.extend(milestones_reached)

        except Exception as e:
            logger.error(f"Error checking milestones: {e}")

        return new_milestones

    def _get_user_achievements(self, user_id: str) -> List[str]:
        """Get user's current achievements."""
        # In a real implementation, this would query the database
        return []  # Placeholder

    def _generate_progress_notification(self, user_id: str, activity_record: Dict,
                                      new_achievements: List[Dict],
                                      new_milestones: List[Dict]) -> Dict:
        """Generate a progress notification for Discord."""
        game = activity_record['game']
        activity_type = activity_record['activity_type']

        notification = {
            'title': f"🎮 Game Progress Update",
            'description': f"Great work in **{game.title()}**!",
            'fields': [],
            'color': 0x3498db
        }

        # Activity completion
        notification['fields'].append({
            'name': 'Activity Completed',
            'value': f"• {activity_type.replace('_', ' ').title()}\n• Tokens Earned: {activity_record.get('tokens_earned', 0)}",
            'inline': False
        })

        # New achievements
        if new_achievements:
            achievement_text = ""
            for achievement in new_achievements:
                achievement_text += f"{achievement['icon']} **{achievement['name']}**\n"
                achievement_text += f"💎 +{achievement['tokens']} tokens\n\n"

            notification['fields'].append({
                'name': '🏆 New Achievements!',
                'value': achievement_text,
                'inline': False
            })

        # New milestones
        if new_milestones:
            milestone_text = ""
            for milestone in new_milestones:
                milestone_text += f"🎯 **{milestone['description']}**\n"
                milestone_text += f"💎 +{milestone['reward_tokens']} tokens\n\n"

            notification['fields'].append({
                'name': '📊 Milestone Reached!',
                'value': milestone_text,
                'inline': False
            })

        # Cape Town context
        if hasattr(cape_town_data, 'get_simulation_data'):
            ct_data = cape_town_data.get_simulation_data('unemployment')
            notification['fields'].append({
                'name': '🌍 Cape Town Impact',
                'value': f"• Local Unemployment: {ct_data.get('baseline_unemployment', 0):.1%}\n"
                        f"• Your activity helps address real community challenges!",
                'inline': False
            })

        return notification

    def _get_personalized_recommendations(self, user_id: str) -> List[Dict]:
        """Get personalized game recommendations based on user progress."""
        recommendations = []

        try:
            # Analyze user activity patterns and suggest next steps
            recommendations = [
                {
                    'game': 'virtonomics',
                    'activity': 'supply_chain_optimization',
                    'reason': 'Build on your logistics skills',
                    'expected_tokens': 50
                },
                {
                    'game': 'cwetlands',
                    'activity': 'water_conservation_project',
                    'reason': 'Address Cape Town water challenges',
                    'expected_tokens': 75
                }
            ]

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")

        return recommendations

    def get_user_progress_report(self, user_id: str) -> Dict:
        """Generate a comprehensive progress report for a user."""
        try:
            # This would typically query user activity history
            progress_report = {
                'user_id': user_id,
                'total_activities': 15,
                'games_explored': ['virtonomics', 'simcompanies'],
                'total_tokens_earned': 450,
                'current_level': 3,
                'achievements_unlocked': 4,
                'skills_developed': ['management', 'logistics', 'sustainability'],
                'cape_town_impact': {
                    'water_conservation_contribution': 0.02,  # 2% of virtual conservation
                    'job_creation_simulated': 8,
                    'policy_discussions_participated': 3
                },
                'next_goals': [
                    'Complete 25 total activities',
                    'Explore CWetlands game',
                    'Achieve business profitability'
                ],
                'recommendations': self._get_personalized_recommendations(user_id)
            }

            return progress_report

        except Exception as e:
            logger.error(f"Error generating progress report: {e}")
            return {'error': str(e)}

    def get_community_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get community leaderboard for game activities."""
        try:
            # This would typically query user statistics
            leaderboard = [
                {'rank': 1, 'user_id': 'user123', 'activities': 45, 'tokens': 1200, 'level': 8},
                {'rank': 2, 'user_id': 'user456', 'activities': 38, 'tokens': 950, 'level': 6},
                {'rank': 3, 'user_id': 'user789', 'activities': 32, 'tokens': 800, 'level': 5}
            ]

            return leaderboard[:limit]

        except Exception as e:
            logger.error(f"Error generating leaderboard: {e}")
            return []

    def get_cape_town_impact_report(self) -> Dict:
        """Generate report on Cape Town community impact from game activities."""
        try:
            impact_report = {
                'total_participants': 150,
                'total_activities_completed': 1250,
                'virtual_jobs_created': 450,
                'water_conservation_simulated': 2500000,  # Liters
                'policy_simulations_run': 75,
                'skills_developed': {
                    'entrepreneurship': 85,
                    'sustainability': 62,
                    'management': 94,
                    'digital_skills': 58
                },
                'community_benefits': [
                    'Increased awareness of local challenges',
                    'Development of practical skills',
                    'Community problem-solving engagement',
                    'Youth empowerment through gamification'
                ],
                'real_world_applications': [
                    'Job seekers gaining business experience',
                    'Community members learning water conservation',
                    'Youth developing entrepreneurial skills',
                    'Policy makers getting data-driven insights'
                ]
            }

            return impact_report

        except Exception as e:
            logger.error(f"Error generating impact report: {e}")
            return {'error': str(e)}

# Global game activity tracker
game_tracker = GameActivityTracker()

def track_game_activity(user_id: str, game: str, activity_type: str,
                       details: Dict = None) -> Dict:
    """Convenience function to track game activity."""
    return game_tracker.track_activity(user_id, game, activity_type, details)

def get_progress_report(user_id: str) -> Dict:
    """Get user progress report."""
    return game_tracker.get_user_progress_report(user_id)

def get_community_stats() -> Dict:
    """Get community statistics."""
    return game_tracker.get_cape_town_impact_report()

if __name__ == "__main__":
    # Test the game activity tracker
    test_user = "test_user_123"

    # Track a sample activity
    result = track_game_activity(test_user, 'virtonomics', 'company_created',
                                {'company_name': 'Test Logistics Ltd'})

    print("Activity Tracking Result:")
    print(json.dumps(result, indent=2))

    # Get progress report
    progress = get_progress_report(test_user)
    print("\nProgress Report:")
    print(json.dumps(progress, indent=2))