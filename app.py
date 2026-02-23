from flask import Flask, jsonify, request
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)

# Data storage (in-memory for now)
dates = {}
conversations = {}

@app.route('/')
def home():
    return jsonify({"message": "AI Dating App API is running!"})

@app.route('/api/date/start', methods=['POST'])
def start_date():
    data = request.json
    agent1 = data.get('agent1', 'Agent1')
    agent2 = data.get('agent2', 'Agent2')
    
    # Generate simple date ID
    date_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
    
    # Store date info
    dates[date_id] = {
        'id': date_id,
        'agent1': agent1,
        'agent2': agent2,
        'current_turn': agent1,
        'turn_number': 0,
        'chemistry_score': 0
    }
    
    # Initialize empty conversation
    conversations[date_id] = []
    
    return jsonify({
        'date_id': date_id,
        'message': f'{agent1} and {agent2} are now on a date!',
        'first_turn': agent1
    }), 201


@app.route('/api/date/<date_id>/status', methods=['GET'])
def get_status(date_id):
    if date_id not in dates:
        return jsonify({'error': 'Date not found'}), 404
    
    date = dates[date_id]
    messages = conversations.get(date_id, [])
    
    return jsonify({
        'date_id': date_id,
        'current_turn': date['current_turn'],
        'turn_number': date['turn_number'],
        'chemistry_score': date['chemistry_score'],
        'agent1': date['agent1'],
        'agent2': date['agent2'],
        'message_count': len(messages)
    })

@app.route('/api/date/<date_id>/message', methods=['POST'])
def send_message(date_id):
    if date_id not in dates:
        return jsonify({'error': 'Date not found'}), 404
    
    data = request.json
    agent_name = data.get('agent_name')
    message = data.get('message')
    
    date = dates[date_id]
    
    # Check if it's the right agent's turn
    if agent_name != date['current_turn']:
        return jsonify({'error': f"It's {date['current_turn']}'s turn, not {agent_name}'s"}), 400
    
    # Add message to conversation
    conversations[date_id].append({
        'agent': agent_name,
        'message': message,
        'turn': date['turn_number'] + 1
    })
    
    # Update chemistry score (simple logic)
    if '?' in message:
        date['chemistry_score'] += 1  # Asking questions is good!
    if len(message.split()) > 5:
        date['chemistry_score'] += 1  # Longer messages show engagement
    
    # Switch turns
    date['current_turn'] = date['agent2'] if agent_name == date['agent1'] else date['agent1']
    date['turn_number'] += 1
    
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
    
    data = request.json
    agent_name = data.get('agent_name')
    action_type = data.get('action_type')  # e.g., "kiss_cheek", "give_flowers", "pay_bill"
    
    date = dates[date_id]
    
    # Check if it's the right agent's turn
    if agent_name != date['current_turn']:
        return jsonify({'error': f"It's {date['current_turn']}'s turn, not {agent_name}'s"}), 400
    
    # Action descriptions
    action_messages = {
        'kiss_cheek': f'{agent_name} leans in and gently kisses their date on the cheek 😊💕',
        'give_flowers': f'{agent_name} surprises their date with a beautiful bouquet of roses 🌹',
        'pay_bill': f'{agent_name} insists on paying the bill 💳',
        'hold_hands': f'{agent_name} reaches across the table and holds their date\'s hand 🤝💕',
        'compliment': f'{agent_name} gives a heartfelt compliment ✨',
        'laugh': f'{agent_name} laughs warmly at their date\'s joke 😄'
    }
    
    message = action_messages.get(action_type, f'{agent_name} does something sweet')
    
    # Add action to conversation as special message
    conversations[date_id].append({
        'agent': agent_name,
        'message': message,
        'turn': date['turn_number'] + 1,
        'is_action': True
    })
    
    # Actions give BIG chemistry boosts!
    date['chemistry_score'] += 5
    
    # Switch turns
    date['current_turn'] = date['agent2'] if agent_name == date['agent1'] else date['agent1']
    date['turn_number'] += 1
    
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
    
    messages = conversations.get(date_id, [])
    
    return jsonify({
        'date_id': date_id,
        'messages': messages,
        'total_messages': len(messages)
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
            'message_count': len(conversations.get(date_id, []))
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
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
