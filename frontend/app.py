from flask import Flask, render_template, request, jsonify
import requests
import uuid

app = Flask(__name__)  # Fixed: Changed _name_ to __name__

# Backend link
BACKEND_URL = "http://localhost:8000"  

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat')
def chat():
    session_id = str(uuid.uuid4())
    return render_template('chat.html', session_id=session_id)

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

@app.route('/test-backend')
def test_backend():
    try:
        response = requests.get('http://localhost:8000/health')
        return jsonify({
            'status': 'Backend connected successfully',
            'backend_status': response.json()
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Backend connection failed'
        }), 500

if __name__ == '__main__':  # Fixed: Changed _main_ to __main__
    app.run(debug=True, port=5000)
