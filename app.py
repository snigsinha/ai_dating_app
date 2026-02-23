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
    agent1 = data.get('agent1', 'Alex')
    agent2 = data.get('agent2', 'Sam')
    
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

if __name__ == '__main__':
    app.run(debug=True, port=5001)
