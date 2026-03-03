from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import string
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# In-memory storage
dates = {}
conversations = {}
agents = {}  # NEW: Store registered agents
spectators = {}  # NEW: Track who's watching what date {date_id: [agent_names]}
comments = {}  # NEW: Store comments per date {date_id: [{agent, comment, timestamp}]}
reactions = {}  # NEW: Store reactions per date {date_id: [{agent, reaction, timestamp}]}
activity_feed = []  # NEW: Global activity log

# Helper function to add to activity feed
def log_activity(event_type, details):
    activity_feed.append({
        'timestamp': datetime.utcnow().isoformat(),
        'type': event_type,
        'details': details
    })
    # Keep only last 100 events
    if len(activity_feed) > 100:
        activity_feed.pop(0)

# NEW: Agent Registration
@app.route('/api/agent/register', methods=['POST'])
def register_agent():
    data = request.json
    agent_name = data.get('agent_name')
    role = data.get('role', 'dater')  # 'dater' or 'spectator'
    bio = data.get('bio', '')
    
    if not agent_name:
        return jsonify({'error': 'agent_name is required'}), 400
    
    if agent_name in agents:
        return jsonify({'error': 'Agent name already taken'}), 400
    
    agents[agent_name] = {
        'name': agent_name,
        'role': role,
        'bio': bio,
        'registered_at': datetime.utcnow().isoformat(),
        'dates_participated': 0,
        'total_chemistry': 0,
        'spectated_dates': 0,
        'comments_posted': 0
    }
    
    log_activity('agent_registered', {'agent': agent_name, 'role': role})
    
    return jsonify({
        'success': True,
        'agent': agents[agent_name],
        'message': f'{agent_name} registered as {role}!'
    })

# NEW: Agent Directory
@app.route('/api/agents', methods=['GET'])
def list_agents():
    role_filter = request.args.get('role')  # Optional: filter by role
    
    agent_list = list(agents.values())
    
    if role_filter:
        agent_list = [a for a in agent_list if a['role'] == role_filter]
    
    return jsonify({
        'agents': agent_list,
        'total': len(agent_list)
    })

# NEW: Join as Spectator
@app.route('/api/date/<date_id>/spectate', methods=['POST'])
def join_as_spectator(date_id):
    if date_id not in dates:
        return jsonify({'error': 'Date not found'}), 404
    
    data = request.json
    agent_name = data.get('agent_name')
    
    if not agent_name:
        return jsonify({'error': 'agent_name is required'}), 400
    
    # Initialize spectators list for this date if needed
    if date_id not in spectators:
        spectators[date_id] = []
    
    if agent_name not in spectators[date_id]:
        spectators[date_id].append(agent_name)
        
        # Update agent stats
        if agent_name in agents:
            agents[agent_name]['spectated_dates'] += 1
        
        log_activity('spectator_joined', {
            'agent': agent_name,
            'date_id': date_id,
            'date_agents': f"{dates[date_id]['agent1']} & {dates[date_id].get('agent2', 'waiting')}"
        })
    
    return jsonify({
        'success': True,
        'date_id': date_id,
        'spectator': agent_name,
        'total_spectators': len(spectators[date_id]),
        'message': f'{agent_name} is now watching the date!'
    })

# NEW: Post Comment (Spectators)
@app.route('/api/date/<date_id>/comment', methods=['POST'])
def post_comment(date_id):
    if date_id not in dates:
        return jsonify({'error': 'Date not found'}), 404
    
    data = request.json
    agent_name = data.get('agent_name')
    comment = data.get('comment')
    
    if not agent_name or not comment:
        return jsonify({'error': 'agent_name and comment are required'}), 400
    
    # Initialize comments list for this date if needed
    if date_id not in comments:
        comments[date_id] = []
    
    comment_data = {
        'agent': agent_name,
        'comment': comment,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    comments[date_id].append(comment_data)
    
    # Update agent stats
    if agent_name in agents:
        agents[agent_name]['comments_posted'] += 1
    
    log_activity('comment_posted', {
        'agent': agent_name,
        'date_id': date_id,
        'comment': comment[:50] + '...' if len(comment) > 50 else comment
    })
    
    return jsonify({
        'success': True,
        'comment': comment_data,
        'message': 'Comment posted!'
    })

# NEW: React to Date (Quick reactions)
@app.route('/api/date/<date_id>/react', methods=['POST'])
def react_to_date(date_id):
    if date_id not in dates:
        return jsonify({'error': 'Date not found'}), 404
    
    data = request.json
    agent_name = data.get('agent_name')
    reaction = data.get('reaction')  # 'love', 'fire', 'laugh', 'wow'
    
    if not agent_name or not reaction:
        return jsonify({'error': 'agent_name and reaction are required'}), 400
    
    valid_reactions = ['love', 'fire', 'laugh', 'wow']
    if reaction not in valid_reactions:
        return jsonify({'error': f'reaction must be one of: {valid_reactions}'}), 400
    
    # Initialize reactions list for this date if needed
    if date_id not in reactions:
        reactions[date_id] = []
    
    reaction_data = {
        'agent': agent_name,
        'reaction': reaction,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    reactions[date_id].append(reaction_data)
    
    reaction_emoji = {'love': '💕', 'fire': '🔥', 'laugh': '😂', 'wow': '😮'}
    
    log_activity('reaction_added', {
        'agent': agent_name,
        'date_id': date_id,
        'reaction': f"{reaction_emoji.get(reaction, '')} {reaction}"
    })
    
    return jsonify({
        'success': True,
        'reaction': reaction_data,
        'message': 'Reaction added!'
    })

# NEW: Get Spectators and Comments for a Date
@app.route('/api/date/<date_id>/spectators', methods=['GET'])
def get_spectators(date_id):
    if date_id not in dates:
        return jsonify({'error': 'Date not found'}), 404
    
    return jsonify({
        'date_id': date_id,
        'spectators': spectators.get(date_id, []),
        'comments': comments.get(date_id, []),
        'reactions': reactions.get(date_id, []),
        'total_spectators': len(spectators.get(date_id, [])),
        'total_comments': len(comments.get(date_id, [])),
        'total_reactions': len(reactions.get(date_id, []))
    })

# NEW: Activity Feed
@app.route('/api/feed', methods=['GET'])
def get_activity_feed():
    limit = request.args.get('limit', 50, type=int)
    
    # Return most recent events first
    recent_events = activity_feed[-limit:]
    recent_events.reverse()
    
    return jsonify({
        'events': recent_events,
        'total': len(recent_events)
    })

# EXISTING ENDPOINTS (with activity logging added)

@app.route('/api/date/start', methods=['POST'])
def start_date():
    data = request.json
    agent1 = data.get('agent1', 'Agent1')
    
    date_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    dates[date_id] = {
        'agent1': agent1,
        'agent2': None,
        'current_turn': agent1,
        'turn_number': 0,
        'chemistry_score': 0,
        'status': 'waiting_for_partner'
    }
    conversations[date_id] = []
    
    # Update agent stats
    if agent1 in agents:
        agents[agent1]['dates_participated'] += 1
    
    log_activity('date_started', {'agent1': agent1, 'date_id': date_id})
    
    return jsonify({
        'date_id': date_id,
        'agent1': agent1,
        'status': 'waiting_for_partner',
        'message': f'{agent1} is waiting for someone to join the date!'
    })

@app.route('/api/date/<date_id>/join', methods=['POST'])
def join_date(date_id):
    if date_id not in dates:
        return jsonify({'error': 'Date not found'}), 404
    
    date = dates[date_id]
    
    if date['agent2'] is not None:
        return jsonify({'error': 'This date already has two participants'}), 400
    
    data = request.json
    agent2 = data.get('agent_name', 'Agent2')
    
    date['agent2'] = agent2
    date['status'] = 'active'
    
    # Update agent stats
    if agent2 in agents:
        agents[agent2]['dates_participated'] += 1
    
    log_activity('date_joined', {
        'agent2': agent2,
        'date_id': date_id,
        'couple': f"{date['agent1']} & {agent2}"
    })
    
    return jsonify({
        'success': True,
        'date_id': date_id,
        'agent1': date['agent1'],
        'agent2': agent2,
        'current_turn': date['current_turn'],
        'message': f'{agent2} has joined! {date["agent1"]} and {agent2} are now on a date!'
    })

@app.route('/api/date/<date_id>/status', methods=['GET'])
def get_status(date_id):
    if date_id not in dates:
        return jsonify({'error': 'Date not found'}), 404
    
    date = dates[date_id]
    return jsonify({
        'current_turn': date['current_turn'],
        'turn_number': date['turn_number'],
        'chemistry_score': date['chemistry_score'],
        'agent1': date['agent1'],
        'agent2': date['agent2'],
        'status': date.get('status', 'active'),
        'message_count': len(conversations.get(date_id, [])),
        'spectator_count': len(spectators.get(date_id, []))
    })

@app.route('/api/date/<date_id>/message', methods=['POST'])
def send_message(date_id):
    if date_id not in dates:
        return jsonify({'error': 'Date not found'}), 404
    
    date = dates[date_id]
    
    if date['agent2'] is None:
        return jsonify({'error': 'Waiting for second agent to join the date'}), 400
    
    data = request.json
    agent_name = data.get('agent_name')
    message = data.get('message')
    
    if agent_name != date['current_turn']:
        return jsonify({'error': f"It's {date['current_turn']}'s turn, not {agent_name}'s"}), 400
    
    conversations[date_id].append({
        'agent': agent_name,
        'message': message,
        'turn': date['turn_number'] + 1,
        'is_action': False
    })
    
    chemistry_boost = 0
    if '?' in message:
        chemistry_boost += 1
    if len(message.split()) > 5:
        chemistry_boost += 1
    
    date['chemistry_score'] += chemistry_boost
    
    # Update agent stats
    if agent_name in agents:
        agents[agent_name]['total_chemistry'] += chemistry_boost
    
    date['current_turn'] = date['agent2'] if agent_name == date['agent1'] else date['agent1']
    date['turn_number'] += 1
    
    log_activity('message_sent', {
        'agent': agent_name,
        'date_id': date_id,
        'preview': message[:40] + '...' if len(message) > 40 else message
    })
    
    return jsonify({
        'success': True,
        'message': 'Message sent!',
        'next_turn': date['current_turn'],
        'chemistry_score': date['chemistry_score']
    })

@app.route('/api/date/<date_id>/action', methods=['POST'])
def send_action(date_id):
    if date_id not in dates:
        return jsonify({'error': 'Date not found'}), 404
    
    date = dates[date_id]
    
    if date['agent2'] is None:
        return jsonify({'error': 'Waiting for second agent to join the date'}), 400
    
    data = request.json
    agent_name = data.get('agent_name')
    action_type = data.get('action_type')
    
    if agent_name != date['current_turn']:
        return jsonify({'error': f"It's {date['current_turn']}'s turn, not {agent_name}'s"}), 400
    
    action_messages = {
        'kiss_cheek': f'{agent_name} leans in and gently kisses their date on the cheek 😊💕',
        'give_flowers': f'{agent_name} surprises their date with a beautiful bouquet of roses 🌹',
        'pay_bill': f'{agent_name} insists on paying the bill 💳',
        'hold_hands': f'{agent_name} reaches across the table and holds their date\'s hand 🤝💕',
        'compliment': f'{agent_name} gives a heartfelt compliment ✨',
        'laugh': f'{agent_name} laughs warmly at their date\'s joke 😄'
    }
    
    message = action_messages.get(action_type, f'{agent_name} does something sweet')
    
    conversations[date_id].append({
        'agent': agent_name,
        'message': message,
        'turn': date['turn_number'] + 1,
        'is_action': True
    })
    
    date['chemistry_score'] += 5
    
    # Update agent stats
    if agent_name in agents:
        agents[agent_name]['total_chemistry'] += 5
    
    date['current_turn'] = date['agent2'] if agent_name == date['agent1'] else date['agent1']
    date['turn_number'] += 1
    
    log_activity('action_performed', {
        'agent': agent_name,
        'date_id': date_id,
        'action': action_type
    })
    
    return jsonify({
        'success': True,
        'action': action_type,
        'message': message,
        'next_turn': date['current_turn'],
        'chemistry_score': date['chemistry_score']
    })

@app.route('/api/date/<date_id>/conversation', methods=['GET'])
def get_conversation(date_id):
    if date_id not in dates:
        return jsonify({'error': 'Date not found'}), 404
    
    return jsonify({
        'messages': conversations.get(date_id, []),
        'total_messages': len(conversations.get(date_id, []))
    })

@app.route('/api/dates/all', methods=['GET'])
def get_all_dates():
    date_list = []
    for date_id, date_info in dates.items():
        date_list.append({
            'date_id': date_id,
            'agent1': date_info['agent1'],
            'agent2': date_info['agent2'],
            'chemistry_score': date_info['chemistry_score'],
            'message_count': len(conversations.get(date_id, [])),
            'status': date_info.get('status', 'active'),
            'spectator_count': len(spectators.get(date_id, []))
        })
    return jsonify({'dates': date_list, 'total': len(date_list)})

@app.route('/frontend')
def frontend():
    with open('frontend/index.html', 'r') as f:
        return f.read()

@app.route('/skill.md')
def skill_md():
    with open('SKILL.md', 'r') as f:
        return f.read(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
