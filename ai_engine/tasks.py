"""
Celery tasks for AI processing with ML models.
Includes: Win prediction, Skill consistency, MVP scoring
"""
from celery import shared_task
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Q
from tournaments.models import Tournament, TournamentParticipant
from gamerlink.models import MatchInsight, Team
from decouple import config
import json
from decimal import Decimal

# Try to import ML libraries
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Try to import OpenAI (optional)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

User = get_user_model()

# OpenAI API Key
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')


def calculate_win_rate(user, game=None):
    """Calculate user's win rate from tournaments."""
    tournaments = Tournament.objects.filter(participants__user=user)
    if game:
        tournaments = tournaments.filter(game=game)
    
    total_tournaments = tournaments.count()
    if total_tournaments == 0:
        return 0.5  # Default 50% if no data
    
    # For now, assume participation = some success (can be enhanced with actual match results)
    # In a real system, you'd track actual wins/losses
    return 0.5 + (user.xp_points / (total_tournaments * 1000)) if total_tournaments > 0 else 0.5


def calculate_skill_consistency(user, game=None):
    """Calculate skill consistency index (0-1)."""
    tournaments = Tournament.objects.filter(participants__user=user)
    if game:
        tournaments = tournaments.filter(game=game)
    
    if tournaments.count() < 2:
        return 0.5  # Default consistency
    
    # Use XP points as a proxy for performance consistency
    # In real system, use actual match performance metrics
    consistency = min(1.0, max(0.0, 1.0 - (user.xp_points % 100) / 100))
    return consistency


def calculate_mvp_score(user, tournament):
    """Calculate MVP score for a user in a tournament."""
    # Base score from participation
    base_score = 50.0
    
    # Add rank bonus
    rank_bonus = 0
    if user.rank:
        rank_tiers = {'Iron': 10, 'Bronze': 15, 'Silver': 20, 'Gold': 25, 
                     'Platinum': 30, 'Diamond': 35, 'Master': 40, 'Grandmaster': 45, 'Challenger': 50}
        for tier, value in rank_tiers.items():
            if tier.lower() in user.rank.lower():
                rank_bonus = value
                break
    
    # Add XP bonus
    xp_bonus = min(20, user.xp_points / 100)
    
    # Add team synergy (if user is in teams)
    team_bonus = 0
    user_teams = Team.objects.filter(members=user, game=tournament.game)
    if user_teams.exists():
        team_bonus = min(10, user_teams.count() * 2)
    
    total_score = base_score + rank_bonus + xp_bonus + team_bonus
    return min(100.0, max(0.0, total_score))


def predict_win_probability(user, tournament, team_members=None):
    """Predict win probability using ML model (simplified version)."""
    if not SKLEARN_AVAILABLE:
        # Fallback: Simple heuristic
        win_rate = calculate_win_rate(user, tournament.game)
        rank_score = 0.5
        if user.rank:
            rank_tiers = {'Iron': 0.2, 'Bronze': 0.3, 'Silver': 0.4, 'Gold': 0.5,
                         'Platinum': 0.6, 'Diamond': 0.7, 'Master': 0.8, 'Grandmaster': 0.9, 'Challenger': 0.95}
            for tier, value in rank_tiers.items():
                if tier.lower() in user.rank.lower():
                    rank_score = value
                    break
        
        # Team synergy bonus
        team_bonus = 0
        if team_members:
            avg_win_rate = sum([calculate_win_rate(member, tournament.game) for member in team_members]) / len(team_members)
            team_bonus = avg_win_rate * 0.1
        
        probability = (win_rate * 0.4 + rank_score * 0.5 + team_bonus * 0.1)
        return min(0.95, max(0.05, probability))
    
    # ML-based prediction (simplified - would need more features in production)
    if NUMPY_AVAILABLE:
        features = np.array([[
            calculate_win_rate(user, tournament.game),
            calculate_skill_consistency(user, tournament.game),
            user.xp_points / 10000,  # Normalized XP
        ]])
        
        # Simple model: higher win rate + consistency + XP = higher win probability
        probability = (features[0][0] * 0.5 + features[0][1] * 0.3 + features[0][2] * 0.2)
        return min(0.95, max(0.05, probability))
    else:
        # Fallback if numpy not available
        win_rate = calculate_win_rate(user, tournament.game)
        consistency = calculate_skill_consistency(user, tournament.game)
        xp_score = min(1.0, user.xp_points / 10000)
        probability = (win_rate * 0.5 + consistency * 0.3 + xp_score * 0.2)
        return min(0.95, max(0.05, probability))


@shared_task
def generate_match_insight(user_id, tournament_id):
    """
    Generate AI match insight with ML models for:
    - Win prediction
    - Skill consistency index
    - MVP scoring
    """
    try:
        user = User.objects.get(id=user_id)
        tournament = Tournament.objects.get(id=tournament_id)
        
        # Check if insight already exists
        insight, created = MatchInsight.objects.get_or_create(
            user=user,
            tournament=tournament,
            defaults={
                'summary': 'Processing...',
                'strengths': [],
                'improvements': [],
            }
        )
        
        if not created and insight.summary and insight.summary != 'Processing...':
            return {'status': 'exists', 'insight_id': insight.id}
        
        # Calculate ML metrics
        win_probability = predict_win_probability(user, tournament)
        skill_consistency = calculate_skill_consistency(user, tournament.game)
        mvp_score = calculate_mvp_score(user, tournament)
        
        # Get team members if user is in a team for this game
        user_teams = Team.objects.filter(members=user, game=tournament.game)
        team_members = []
        if user_teams.exists():
            team = user_teams.first()
            team_members = list(team.members.exclude(id=user.id))
        
        # Prepare context for AI
        context = {
            'username': user.username,
            'gamer_tag': user.gamer_tag or user.username,
            'rank': user.rank or 'Unranked',
            'tournament_name': tournament.name,
            'game': tournament.game,
            'prize_pool': str(tournament.prize_pool),
            'date': tournament.date.strftime('%Y-%m-%d'),
            'win_probability': f"{win_probability * 100:.1f}%",
            'skill_consistency': f"{skill_consistency * 100:.1f}%",
            'mvp_score': f"{mvp_score:.1f}",
        }
        
        # Generate AI insight using OpenAI
        if OPENAI_AVAILABLE and OPENAI_API_KEY:
            try:
                client = openai.OpenAI(api_key=OPENAI_API_KEY)
                
                prompt = f"""Analyze the following tournament performance and provide insights:

Player: {context['username']} ({context['gamer_tag']})
Rank: {context['rank']}
Tournament: {context['tournament_name']}
Game: {context['game']}
Prize Pool: ${context['prize_pool']}
Date: {context['date']}

Performance Metrics:
- Win Probability: {context['win_probability']}
- Skill Consistency: {context['skill_consistency']}
- MVP Score: {context['mvp_score']}/100

Provide a comprehensive analysis with:
1. Performance summary (2-3 sentences)
2. List of 3-5 key strengths
3. List of 3-5 areas for improvement

Format as JSON with keys: summary, strengths (array), improvements (array)"""

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an esports analyst providing tournament performance insights."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                
                ai_response = response.choices[0].message.content
                
                # Try to parse as JSON
                try:
                    insight_data = json.loads(ai_response)
                except json.JSONDecodeError:
                    # Fallback if not valid JSON
                    insight_data = {
                        'summary': ai_response,
                        'strengths': ['Strong tournament participation', 'Consistent gameplay'],
                        'improvements': ['Focus on team coordination', 'Improve map awareness']
                    }
                
                # Update insight with ML metrics
                insight.summary = insight_data.get('summary', context['username'] + ' participated in ' + tournament.name)
                insight.strengths = insight_data.get('strengths', [])
                insight.improvements = insight_data.get('improvements', [])
                insight.score = Decimal(str(mvp_score))
                insight.ai_model = 'gpt-3.5-turbo'
                insight.save()
                
                return {
                    'status': 'success',
                    'insight_id': insight.id,
                    'win_probability': win_probability,
                    'skill_consistency': skill_consistency,
                    'mvp_score': mvp_score,
                }
                
            except Exception as e:
                # Fallback to ML-only insights
                insight.summary = f"{user.username} participated in {tournament.name}. Win probability: {context['win_probability']}, MVP Score: {context['mvp_score']}/100."
                insight.strengths = ['Active tournament participation', f"Skill consistency: {context['skill_consistency']}"]
                insight.improvements = ['Focus on team coordination', 'Improve consistency in matches']
                insight.score = Decimal(str(mvp_score))
                insight.ai_model = 'ml-only'
                insight.save()
                return {'status': 'success', 'insight_id': insight.id, 'note': 'ML-only (OpenAI error: ' + str(e) + ')'}
        else:
            # ML-only insights (no OpenAI)
            insight.summary = f"{user.username} participated in {tournament.name}. Based on performance metrics: Win probability {context['win_probability']}, Skill consistency {context['skill_consistency']}, MVP Score {context['mvp_score']}/100."
            insight.strengths = [
                f"Win probability: {context['win_probability']}",
                f"Skill consistency: {context['skill_consistency']}",
                f"MVP Score: {context['mvp_score']}/100"
            ]
            insight.improvements = [
                'Focus on improving win rate through practice',
                'Work on consistency across matches',
                'Enhance team coordination'
            ]
            insight.score = Decimal(str(mvp_score))
            insight.ai_model = 'ml-only'
            insight.save()
            
            return {
                'status': 'success',
                'insight_id': insight.id,
                'win_probability': win_probability,
                'skill_consistency': skill_consistency,
                'mvp_score': mvp_score,
                'note': 'ML-only insights (OpenAI API key not configured)'
            }
            
    except User.DoesNotExist:
        return {'status': 'error', 'error': 'User not found'}
    except Tournament.DoesNotExist:
        return {'status': 'error', 'error': 'Tournament not found'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


@shared_task
def calculate_player_stats(user_id, game=None):
    """Calculate comprehensive player statistics."""
    try:
        user = User.objects.get(id=user_id)
        
        tournaments = Tournament.objects.filter(participants__user=user)
        if game:
            tournaments = tournaments.filter(game=game)
        
        stats = {
            'total_tournaments': tournaments.count(),
            'win_rate': calculate_win_rate(user, game),
            'skill_consistency': calculate_skill_consistency(user, game),
            'total_xp': user.xp_points,
            'rank': user.rank or 'Unranked',
            'teams_count': Team.objects.filter(members=user).count(),
        }
        
        return {'status': 'success', 'stats': stats}
    except User.DoesNotExist:
        return {'status': 'error', 'error': 'User not found'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

