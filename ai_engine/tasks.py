"""
Celery tasks for AI processing.
"""
from celery import shared_task
from django.contrib.auth import get_user_model
from tournaments.models import Tournament
from gamerlink.models import MatchInsight
from decouple import config
import json

# Try to import OpenAI (optional)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

User = get_user_model()

# OpenAI API Key
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')

@shared_task
def generate_match_insight(user_id, tournament_id):
    """
    Generate AI match insight for a user's tournament performance.
    
    Args:
        user_id: ID of the user
        tournament_id: ID of the tournament
    """
    try:
        user = User.objects.get(id=user_id)
        tournament = Tournament.objects.get(id=tournament_id)
        
        # Check if insight already exists
        insight, created = MatchInsight.objects.get_or_create(
            user=user,
            tournament=tournament,
            defaults={'status': 'processing'}
        )
        
        if not created and insight.status == 'completed':
            return {'status': 'exists', 'insight_id': insight.id}
        
        # Prepare context for AI
        context = {
            'username': user.username,
            'gamer_tag': user.gamer_tag,
            'rank': user.rank or 'Unranked',
            'tournament_name': tournament.name,
            'game': tournament.game,
            'prize_pool': str(tournament.prize_pool),
            'date': tournament.date.strftime('%Y-%m-%d'),
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

Provide a brief analysis (2-3 sentences) with:
1. Performance assessment
2. Areas for improvement
3. Positive highlights

Format as JSON with keys: assessment, improvements, highlights"""

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an esports analyst providing tournament performance insights."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.7
                )
                
                ai_response = response.choices[0].message.content
                
                # Try to parse as JSON, fallback to plain text
                try:
                    insight_data = json.loads(ai_response)
                except json.JSONDecodeError:
                    insight_data = {
                        'assessment': ai_response,
                        'improvements': 'Continue practicing and analyzing gameplay.',
                        'highlights': 'Participated in tournament.'
                    }
                
                # Update insight
                insight.ai_summary = json.dumps(insight_data)
                insight.status = 'completed'
                insight.save()
                
                return {
                    'status': 'success',
                    'insight_id': insight.id,
                    'summary': insight_data
                }
                
            except Exception as e:
                insight.status = 'failed'
                insight.error_message = str(e)
                insight.save()
                return {'status': 'error', 'error': str(e)}
        else:
            # Fallback: Generate mock insight if API key not configured
            mock_insight = {
                'assessment': f"{user.username} participated in {tournament.name}. Good effort in the tournament.",
                'improvements': 'Focus on team coordination and map awareness.',
                'highlights': f'Competed in {tournament.game} tournament with ${tournament.prize_pool} prize pool.'
            }
            
            insight.ai_summary = json.dumps(mock_insight)
            insight.status = 'completed'
            insight.save()
            
            return {
                'status': 'success',
                'insight_id': insight.id,
                'summary': mock_insight,
                'note': 'Mock insight (OpenAI API key not configured)'
            }
            
    except User.DoesNotExist:
        return {'status': 'error', 'error': 'User not found'}
    except Tournament.DoesNotExist:
        return {'status': 'error', 'error': 'Tournament not found'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

