from flask import Flask, request, jsonify, render_template
import pymongo
from datetime import datetime
import pprint


app = Flask(__name__)

client = pymongo.MongoClient("<your mongodb connection string>")
db = client['github_webhooks']
collection = db['events']


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        data = request.json
        event_type = request.headers.get('X-GitHub-Event')
        author = data['sender']['login']
        timestamp = datetime.now().strftime("%d %B %Y - %I:%M:%S %p UTC")

        if event_type == 'push':
            request_id = data['head_commit']['id']
            branch = data['ref'].split('/')[-1]
            event = {
                'request_id': request_id,
                'author': author,
                'event_type': 'push',
                'from_branch': branch,
                'to_branch': branch,
                'timestamp': timestamp
            }
        elif event_type == 'pull_request':
            request_id = data['pull_request']['id']
            from_branch = data['pull_request']['head']['ref']
            to_branch = data['pull_request']['base']['ref']
            event = {
                'request_id': request_id,
                'author': author,
                'event_type': 'pull_request',
                'from_branch': from_branch,
                'to_branch': to_branch,
                'timestamp': timestamp
            }
        elif event_type == 'merge_group':
            request_id = data['merge_group']['head_commit']['id']
            from_branch = data['merge_group']['head_ref']
            to_branch = data['pull_request']['base_ref']
            event = {
                'request_id': request_id,
                'author': author,
                'event_type': 'merge',
                'from_branch': from_branch,
                'to_branch': to_branch,
                'timestamp': timestamp
            }

        collection.insert_one(event)
        print(event)
        return jsonify({'status': 'success'}), 200


@app.route('/events', methods=['GET'])
def get_events():
    try:
        events = list(collection.find().sort('timestamp', -1))
        
        response_data = []
        for event in events:
            response_data.append({
                'request_id': event.get('request_id'),
                'author': event.get('author'),
                'event_type': event.get('event_type'),
                'from_branch': event.get('from_branch'),
                'to_branch': event.get('to_branch'),
                'timestamp': event.get('timestamp'),
            })
        
        return jsonify(response_data), 200
    
    except Exception as e:
        print(f"Error fetching events: {e}")
        return jsonify({'status': 'failure'}), 500
    
    
if __name__ == '__main__':
    app.run(port=5000, debug=True)
