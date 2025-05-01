from flask import Flask, render_template, request, jsonify
import requests
import uuid

app = Flask(__name__)

# Backend link
BACKEND_URL = "https://asha-3a9x.onrender.com"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        user_message = request.form['message']
        
        return jsonify({'reply': 'Message received', 'user_message': user_message})
    else:
        return render_template('chat.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/browse')
def browse():
    return render_template('browse.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template('login.html')

# API Proxy Endpoints
@app.route('/api/chat', methods=['POST'])
def proxy_chat():
    try:
        data = request.json
        response = requests.post(
            f'{BACKEND_URL}/chat',
            json={
                "session_id": data.get("session_id"),
                "message": data.get("message"),
                "location": data.get("location", "")
            },
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({
            'reply': "I'm having trouble connecting to Asha AI. Please try again later.",
            'error': str(e)
        }), 502

@app.route('/api/signup', methods=['POST'])
def proxy_signup():
    try:
        data = request.json
        response = requests.post(
            f'{BACKEND_URL}/signup',
            json={
                "name": data.get("name"),
                "email": data.get("email"),
                "password": data.get("password")
            },
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'message': "I'm having trouble connecting to the backend. Please try again later.",
            'error': str(e)
        }), 502

@app.route('/api/login', methods=['POST'])
def proxy_login():
    try:
        data = request.json
        response = requests.post(
            f'{BACKEND_URL}/login',
            json={
                "email": data.get("email"),
                "password": data.get("password")
            },
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'message': "I'm having trouble connecting to the backend. Please try again later.",
            'error': str(e)
        }), 502

if __name__ == '__main__':
    app.run(debug=True, port=5000)
