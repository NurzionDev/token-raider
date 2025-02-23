from flask import Flask, render_template, request, jsonify
import threading
import requests
import time

app = Flask(__name__)

class Worker(threading.Thread):
    def __init__(self, token, channel_ids, message, cooldown, logs):
        super().__init__()
        self.token = token
        self.channel_ids = channel_ids.split(',')
        self.message = message
        self.cooldown = int(cooldown)
        self._stop_event = threading.Event()
        self.logs = logs

    def run(self):
        while not self._stop_event.is_set():
            for channel_id in self.channel_ids:
                url = f'https://discord.com/api/v9/channels/{channel_id}/messages'
                headers = {'Authorization': self.token, 'Content-Type': 'application/json'}
                payload = {'content': self.message}

                try:
                    response = requests.post(url, headers=headers, json=payload)

                    if response.status_code == 200:
                        self.logs.append(f"[+] Message sent to {channel_id} with token {self.token[:5]}***.")
                    elif response.status_code == 429:
                        retry_after = response.json().get('retry_after', 0) / 1000
                        self.logs.append(f"[-] Rate limit reached, retrying after {retry_after} seconds...")
                        time.sleep(retry_after)
                    else:
                        self.logs.append(f"[-] Failed to send message to {channel_id}: {response.status_code}")
                except Exception as e:
                    self.logs.append(f"Error: {e} with token {self.token[:5]}***")
                time.sleep(self.cooldown / 1000)

    def stop(self):
        self._stop_event.set()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_token_details', methods=['POST'])
def get_token_details():
    token_file = request.files.get('token_file')
    if not token_file:
        return jsonify({"status": "error", "message": "No file uploaded."}), 400

    # Assuming the first token is valid for fetching user details
    token = token_file.read().decode('utf-8').splitlines()[0]

    # Here you would normally fetch details via Discord API (bot or user token endpoint)
    # For example, using token to fetch user info (this is just an example and should be done properly)
    user_details = {
        "token": token,
        "username": "DiscordUser",
        "created_at": "2022-01-01",
        "server_id": "1234567890"
    }
    return jsonify({"status": "success", "details": user_details})

@app.route('/start_spam', methods=['POST'])
def start_spam():
    data = request.get_json()
    token = data['token']
    channel_ids = data['channel_ids']
    message = data['message']
    cooldown = data['cooldown']

    logs = []
    worker = Worker(token, channel_ids, message, cooldown, logs)
    worker.start()

    return jsonify({"status": "success", "message": "Spamming started!"})

@app.route('/stop_spam', methods=['POST'])
def stop_spam():
    return jsonify({"status": "success", "message": "Spamming stopped!"})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
