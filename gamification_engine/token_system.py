"""
Token System and Gamification Module

This module implements a comprehensive gamification system for the Job Application Agent:
- Token earning and spending
- Achievement tracking
- Leaderboards
- Reward redemption
- Activity monitoring
- MongoDB integration for persistence

Features:
- Earn tokens for job applications, game activities, course completions
- Redeem tokens for premium features and services
- Track achievements and milestones
- Social comparison through leaderboards
- POPIA-compliant data handling
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import MongoDB
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
    MONGODB_AVAILABLE = True
except ImportError:
    logger.warning("MongoDB not available. Using in-memory storage.")
    MONGODB_AVAILABLE = False

class TokenSystem:
    """Main token system class with MongoDB integration."""

    def __init__(self):
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.database_name = os.getenv('MONGODB_DATABASE', 'job_application_agent')
        self.client = None
        self.db = None

        # Initialize MongoDB connection
        if MONGODB_AVAILABLE:
            try:
                self.client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
                self.client.admin.command('ping')  # Test connection
                self.db = self.client[self.database_name]
                logger.info("Connected to MongoDB for token system")
            except ConnectionFailure:
                logger.warning("MongoDB connection failed. Using in-memory storage.")
                self.client = None
                self.db = None
        else:
            logger.info("Using in-memory storage for token system")

        # In-memory storage as fallback
        self.memory_storage = {
            'users': {},
            'achievements': {},
            'leaderboard': {},
            'transactions': []
        }

        # Token earning rates
        self.earning_rates = {
            'job_application': 10,
            'game_activity_completion': 50,
            'course_completion': 25,
            'skill_assessment': 15,
            'profile_optimization': 30,
            'social_impact_action': 100,
            'referral_bonus': 200,
            'milestone_achievement': 75
        }

        # Achievement definitions
        self.achievements = {
            'first_job_application': {'name': 'First Steps', 'description': 'Applied to your first job', 'tokens': 25, 'icon': '🎯'},
            'job_seeker': {'name': 'Job Seeker', 'description': 'Applied to 10 jobs', 'tokens': 100, 'icon': '💼'},
            'career_builder': {'name': 'Career Builder', 'description': 'Applied to 50 jobs', 'tokens': 500, 'icon': '🚀'},
            'game_explorer': {'name': 'Game Explorer', 'description': 'Completed 5 game activities', 'tokens': 150, 'icon': '🎮'},
            'skill_master': {'name': 'Skill Master', 'description': 'Completed 10 courses', 'tokens': 300, 'icon': '🎓'},
            'social_impact': {'name': 'Social Impact', 'description': 'Participated in 3 social initiatives', 'tokens': 250, 'icon': '🌍'},
            'community_leader': {'name': 'Community Leader', 'description': 'Referred 5 friends', 'tokens': 400, 'icon': '👑'}
        }

        # Reward catalog
        self.reward_catalog = {
            'premium_job_listings': {'name': 'Premium Job Listings', 'cost': 100, 'description': 'Access to exclusive job opportunities'},
            'career_coaching': {'name': 'Career Coaching Session', 'cost': 200, 'description': '1-hour session with career advisor'},
            'linkedin_optimization': {'name': 'LinkedIn Profile Optimization', 'cost': 500, 'description': 'Professional LinkedIn profile enhancement'},
            'resume_review': {'name': 'Resume Review Service', 'cost': 150, 'description': 'Expert resume review and feedback'},
            'skill_assessment': {'name': 'Advanced Skill Assessment', 'cost': 75, 'description': 'Detailed skills evaluation'},
            'networking_event': {'name': 'Virtual Networking Event', 'cost': 300, 'description': 'Access to exclusive networking events'}
        }

    def get_user_profile(self, user_id: str) -> Dict:
        """Get or create user profile."""
        if self.db:
            # MongoDB implementation
            user_doc = self.db.users.find_one({'user_id': user_id})
            if not user_doc:
                user_doc = self._create_new_user(user_id)
                self.db.users.insert_one(user_doc)
            return user_doc
        else:
            # In-memory implementation
            if user_id not in self.memory_storage['users']:
                self.memory_storage['users'][user_id] = self._create_new_user(user_id)
            return self.memory_storage['users'][user_id]

    def _create_new_user(self, user_id: str) -> Dict:
        """Create new user profile."""
        return {
            'user_id': user_id,
            'tokens': 100,  # Welcome bonus
            'total_earned': 100,
            'total_spent': 0,
            'level': 1,
            'xp': 0,
            'achievements': [],
            'activities': [],
            'rewards_redeemed': [],
            'created_at': datetime.now(),
            'last_active': datetime.now(),
            'privacy_settings': {
                'data_sharing': False,
                'leaderboard_visible': True,
                'analytics_opt_in': True
            }
        }

    def earn_tokens(self, user_id: str, activity_type: str, metadata: Dict = None) -> Dict:
        """Award tokens for completing activities."""
        try:
            if activity_type not in self.earning_rates:
                return {'error': f'Unknown activity type: {activity_type}'}

            tokens_earned = self.earning_rates[activity_type]
            user_profile = self.get_user_profile(user_id)

            # Apply multipliers based on user level or streaks
            multiplier = self._calculate_multiplier(user_profile, activity_type)
            tokens_earned = int(tokens_earned * multiplier)

            # Update user profile
            user_profile['tokens'] += tokens_earned
            user_profile['total_earned'] += tokens_earned
            user_profile['xp'] += tokens_earned // 2  # XP = tokens / 2
            user_profile['last_active'] = datetime.now()

            # Check for level up
            new_level = self._calculate_level(user_profile['xp'])
            if new_level > user_profile['level']:
                level_up_bonus = (new_level - user_profile['level']) * 50
                user_profile['tokens'] += level_up_bonus
                user_profile['total_earned'] += level_up_bonus
                user_profile['level'] = new_level

            # Record activity
            activity_record = {
                'type': activity_type,
                'tokens_earned': tokens_earned,
                'timestamp': datetime.now(),
                'metadata': metadata or {}
            }
            user_profile['activities'].append(activity_record)

            # Check for achievements
            new_achievements = self._check_achievements(user_profile)
            for achievement in new_achievements:
                if achievement not in user_profile['achievements']:
                    user_profile['achievements'].append(achievement)
                    achievement_bonus = self.achievements[achievement]['tokens']
                    user_profile['tokens'] += achievement_bonus
                    user_profile['total_earned'] += achievement_bonus

            # Save to database
            self._save_user_profile(user_profile)

            return {
                'success': True,
                'tokens_earned': tokens_earned,
                'new_balance': user_profile['tokens'],
                'level': user_profile['level'],
                'new_achievements': new_achievements,
                'multiplier': multiplier
            }

        except Exception as e:
            logger.error(f"Error earning tokens for user {user_id}: {e}")
            return {'error': str(e)}

    def spend_tokens(self, user_id: str, reward_id: str) -> Dict:
        """Redeem tokens for rewards."""
        try:
            if reward_id not in self.reward_catalog:
                return {'error': f'Unknown reward: {reward_id}'}

            reward = self.reward_catalog[reward_id]
            user_profile = self.get_user_profile(user_id)

            if user_profile['tokens'] < reward['cost']:
                return {'error': 'Insufficient tokens'}

            # Deduct tokens
            user_profile['tokens'] -= reward['cost']
            user_profile['total_spent'] += reward['cost']
            user_profile['last_active'] = datetime.now()

            # Record redemption
            redemption_record = {
                'reward_id': reward_id,
                'cost': reward['cost'],
                'timestamp': datetime.now(),
                'status': 'pending'  # Could be 'delivered', 'cancelled', etc.
            }
            user_profile['rewards_redeemed'].append(redemption_record)

            # Save to database
            self._save_user_profile(user_profile)

            return {
                'success': True,
                'reward': reward['name'],
                'cost': reward['cost'],
                'new_balance': user_profile['tokens'],
                'redemption_id': len(user_profile['rewards_redeemed']) - 1
            }

        except Exception as e:
            logger.error(f"Error spending tokens for user {user_id}: {e}")
            return {'error': str(e)}

    def _calculate_multiplier(self, user_profile: Dict, activity_type: str) -> float:
        """Calculate earning multiplier based on user profile."""
        multiplier = 1.0

        # Level bonus
        multiplier += (user_profile['level'] - 1) * 0.1

        # Activity streak bonus (simplified)
        recent_activities = [a for a in user_profile['activities'][-5:] if a['type'] == activity_type]
        if len(recent_activities) >= 3:
            multiplier += 0.25  # 25% bonus for streaks

        # Achievement bonus
        if user_profile['achievements']:
            multiplier += len(user_profile['achievements']) * 0.05

        return min(multiplier, 2.0)  # Cap at 2x multiplier

    def _calculate_level(self, xp: int) -> int:
        """Calculate user level based on XP."""
        # Simple level calculation: level = sqrt(xp / 100)
        import math
        return max(1, int(math.sqrt(xp / 100)) + 1)

    def _check_achievements(self, user_profile: Dict) -> List[str]:
        """Check for newly unlocked achievements."""
        new_achievements = []

        activities = user_profile['activities']

        # Count activities by type
        activity_counts = {}
        for activity in activities:
            activity_type = activity['type']
            activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1

        # Check achievement conditions
        if activity_counts.get('job_application', 0) >= 1 and 'first_job_application' not in user_profile['achievements']:
            new_achievements.append('first_job_application')

        if activity_counts.get('job_application', 0) >= 10 and 'job_seeker' not in user_profile['achievements']:
            new_achievements.append('job_seeker')

        if activity_counts.get('job_application', 0) >= 50 and 'career_builder' not in user_profile['achievements']:
            new_achievements.append('career_builder')

        if activity_counts.get('game_activity_completion', 0) >= 5 and 'game_explorer' not in user_profile['achievements']:
            new_achievements.append('game_explorer')

        if activity_counts.get('course_completion', 0) >= 10 and 'skill_master' not in user_profile['achievements']:
            new_achievements.append('skill_master')

        return new_achievements

    def _save_user_profile(self, user_profile: Dict):
        """Save user profile to database."""
        if self.db:
            self.db.users.replace_one(
                {'user_id': user_profile['user_id']},
                user_profile,
                upsert=True
            )
        else:
            self.memory_storage['users'][user_profile['user_id']] = user_profile

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top users by tokens earned."""
        if self.db:
            pipeline = [
                {'$sort': {'total_earned': -1}},
                {'$limit': limit},
                {'$project': {'user_id': 1, 'total_earned': 1, 'level': 1, 'achievements': {'$size': '$achievements'}}}
            ]
            results = list(self.db.users.aggregate(pipeline))
        else:
            # In-memory implementation
            users = list(self.memory_storage['users'].values())
            users.sort(key=lambda x: x['total_earned'], reverse=True)
            results = users[:limit]

        return results

    def get_user_stats(self, user_id: str) -> Dict:
        """Get comprehensive user statistics."""
        user_profile = self.get_user_profile(user_id)

        # Calculate statistics
        activities = user_profile['activities']
        activity_counts = {}
        for activity in activities:
            activity_type = activity['type']
            activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1

        # Calculate rank
        if self.db:
            rank = self.db.users.count_documents({'total_earned': {'$gt': user_profile['total_earned']}}) + 1
        else:
            all_users = list(self.memory_storage['users'].values())
            higher_earned = [u for u in all_users if u['total_earned'] > user_profile['total_earned']]
            rank = len(higher_earned) + 1

        return {
            'user_id': user_id,
            'current_tokens': user_profile['tokens'],
            'total_earned': user_profile['total_earned'],
            'total_spent': user_profile['total_spent'],
            'level': user_profile['level'],
            'xp': user_profile['xp'],
            'rank': rank,
            'achievements_count': len(user_profile['achievements']),
            'activities_count': len(activities),
            'activity_breakdown': activity_counts,
            'achievements': user_profile['achievements']
        }

    def anonymize_user_data(self, user_id: str) -> bool:
        """Anonymize user data for POPIA compliance."""
        try:
            if self.db:
                # Replace user data with anonymized version
                anonymized_profile = {
                    'user_id': f"anon_{hash(user_id) % 10000}",
                    'tokens': 0,
                    'total_earned': 0,
                    'total_spent': 0,
                    'level': 1,
                    'xp': 0,
                    'achievements': [],
                    'activities': [],
                    'rewards_redeemed': [],
                    'anonymized_at': datetime.now(),
                    'original_user_id': hash(user_id)  # Keep hash for reference
                }
                self.db.users.replace_one(
                    {'user_id': user_id},
                    anonymized_profile,
                    upsert=True
                )
            else:
                # In-memory anonymization
                if user_id in self.memory_storage['users']:
                    del self.memory_storage['users'][user_id]

            logger.info(f"User data anonymized for {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error anonymizing user data for {user_id}: {e}")
            return False

    def export_user_data(self, user_id: str) -> Dict:
        """Export user data for POPIA compliance."""
        user_profile = self.get_user_profile(user_id)

        # Remove sensitive information
        export_data = {
            'user_id': user_id,
            'export_date': datetime.now(),
            'tokens': user_profile['tokens'],
            'total_earned': user_profile['total_earned'],
            'total_spent': user_profile['total_spent'],
            'level': user_profile['level'],
            'achievements': user_profile['achievements'],
            'activities': user_profile['activities'],  # Anonymize if needed
            'rewards_redeemed': user_profile['rewards_redeemed']
        }

        return export_data

# Global token system instance
token_system = TokenSystem()

def award_tokens(user_id: str, activity_type: str, metadata: Dict = None) -> Dict:
    """Convenience function to award tokens."""
    return token_system.earn_tokens(user_id, activity_type, metadata)

def redeem_reward(user_id: str, reward_id: str) -> Dict:
    """Convenience function to redeem rewards."""
    return token_system.spend_tokens(user_id, reward_id)

def get_user_tokens(user_id: str) -> int:
    """Get user's current token balance."""
    profile = token_system.get_user_profile(user_id)
    return profile['tokens']

def get_available_rewards() -> Dict:
    """Get catalog of available rewards."""
    return token_system.reward_catalog

def get_user_leaderboard_position(user_id: str) -> Dict:
    """Get user's position on leaderboard."""
    stats = token_system.get_user_stats(user_id)
    return {
        'rank': stats['rank'],
        'total_users': len(token_system.memory_storage['users']) if not token_system.db else token_system.db.users.count_documents({}),
        'tokens': stats['current_tokens']
    }

if __name__ == "__main__":
    # Test the token system
    test_user = "test_user_123"

    # Test earning tokens
    result = award_tokens(test_user, 'job_application', {'job_title': 'Software Engineer'})
    print(f"Earned tokens: {result}")

    # Test spending tokens
    result = redeem_reward(test_user, 'premium_job_listings')
    print(f"Redeemed reward: {result}")

    # Test user stats
    stats = token_system.get_user_stats(test_user)
    print(f"User stats: {stats}")