from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from google.cloud import pubsub_v1

import os
import json
import threading

from google.cloud import bigquery
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Google cloud pub/sub setup
PROJECT_ID = 'eattheapple'
TOPIC_ID = 'chat-messages'
SUBSCRIPTION_ID = 'chat-sub'

publisher = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()

topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

# Store online users in memory
online_users = {}

# Publish message to pub/sub
def publish_message(username, text):
    data = json.dumps({'username': username, 'text': text}).encode('utf-8')
    publisher.publish(topic_path,data)
    print(f"Published to Pub/Sub: {username}: {text}")

# Listen to Pub/Sub and broadcast to all WebSocket users
def listen_for_messages():
    def callback(message):
        data = json.loads(message.data.decode('utf-8'))
        socketio.emit('message', {
            'username': data['username'],
            'text': data['text']
        })
        message.ack()
        log_message_to_bigquery(data['username'], data['text'])
    subscriber.subscribe(subscription_path, callback=callback)
    print("Listening to Pub/Sub")

# Start Pub/Sub listener in the background
thread = threading.Thread(target=listen_for_messages)
thread.daemon = True
thread.start()

# BigQuery setup
bq_client = bigquery.Client()
TABLE_ID = 'eattheapple.chat_analytics.messages'

def log_message_to_bigquery(username, text):
    timestamp = datetime.utcnow().isoformat()
    word_count = len(text.split())
    rows_to_insert = [{
        'username': username,
        'message': text,
        'word_count': word_count,
        'timestamp': timestamp
    }]
    errors = bq_client.insert_rows_json(TABLE_ID, rows_to_insert)
    if errors:
        print(f"Error inserting into BigQuery: {errors}")
    else:
        print(f"Logged message to BigQuery: {username}: {text}")

# Flask routes and SocketIO events
@app.route('/')
def home():
    return {"message": "Chatroom backend is running"}

@socketio.on('connect')
def handle_connect():
    print(f"Connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    username = online_users.pop(request.sid, None)
    if username:
        emit('user_left', {'username': username}, broadcast=True)
        emit('online_users', list(online_users.values()), broadcast=True)

@socketio.on('join')
def handle_join(data):
    username = data['username']
    online_users[request.sid] = username
    emit('user_joined', {'username': username}, broadcast=True)
    emit('online_users', list(online_users.values()), broadcast=True)

@socketio.on('message')
def handle_message(data):
    publish_message(data['username'], data['text'])

# Stats
@app.route('/stats')
def get_stats():
    query = """
        SELECT
            username,
            COUNT(*) as message_count,
            AVG(COALESCE(word_count, ARRAY_LENGTH(SPLIT(message, ' ')))) as avg_words
        FROM `eattheapple.chat_analytics.messages`
        GROUP BY username
        ORDER BY message_count DESC
    """
    results = bq_client.query(query).result()
    stats = []
    
    for row in results:
        stats.append({
            'username': row.username,
            'message_count': row.message_count,
            'avg_words': row.avg_words
        })
    return jsonify(stats)

if __name__ == '__main__':
    socketio.run(app, debug=True)