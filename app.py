import json
import time
from flask import Flask, request, jsonify, Response, g
from db import init_db, save_token, delete_token, get_all_tokens
from modules import validate_token, generate_token, proxy_request, log_request
from config import config

app = Flask(__name__)

# Global tokens variable to store tokens in memory
tokens = []

def retrieve_tokens():
    """Retrieve all tokens from the database or return default if none exist"""
    db_tokens = get_all_tokens()
    if db_tokens:
        print('Tokens found in DB')
        return db_tokens
    print('No tokens were found, generating root instead')
    return [{"token": config['DB']['root_token'], "scope": "infer:write:revoke", "expired_at": None}]

# Initialize database and load tokens into memory
def setup():
    init_db()
    global tokens
    tokens = retrieve_tokens()

# Middleware to check for token in all requests
@app.before_request
def check_token():
    if request.method == 'OPTIONS':
        return None

    token = None
    if request.is_json:
        data = request.get_json(silent=True)
        if data and 'token' in data:
            token = data.get('token')
    if not token:
        return jsonify({"error": "Authentication token required"}), 401

    global tokens
    is_valid, scopes = validate_token(token, tokens)
    if not is_valid:
        return jsonify({"error": "Invalid token"}), 401

    # Store scopes in request context for later use in db logs
    g.token = token
    request.scopes = scopes

@app.after_request
def after_request(response):
    log_request(g.get('token'), request.path, request.method, response.status_code)
    return response



@app.route('/create_token', methods=['POST'])
def create_token():
    # Check if user has write scope
    if 'write' not in request.scopes:
        return jsonify({"error": "Insufficient permissions"}), 403

    # Get request data
    data = request.get_json()
    if not data or 'scope' not in data:
        return jsonify({"error": "Scope is required"}), 400

    # Validate requested scopes
    requested_scopes = data['scope'].split(':')
    valid_scopes = ['infer', 'write', 'revoke']
    for scope in requested_scopes:
        if scope not in valid_scopes:
            return jsonify({"error": f"Invalid scope: {scope}"}), 400

    # Generate new token
    new_token = generate_token()
    expired_at = data.get('expired_at')

    # Save token to database
    save_token(new_token, data['scope'], expired_at)

    # Update RAM-ed tokens
    global tokens
    tokens.append({"token": new_token, "scope": data['scope'], "expired_at": expired_at})

    return jsonify({"token": new_token, "scope": data['scope'], "expired_at": expired_at}), 201

@app.route('/revoke_token', methods=['POST'])
def revoke_token():
    if 'revoke' not in request.scopes:
        return jsonify({"error": "Insufficient permissions"}), 403

    # Get token to revoke
    data = request.get_json()
    if not data or 'token' not in data:
        return jsonify({"error": "Token to revoke is required"}), 400

    token_to_revoke = data['token']

    # Check if token exists
    global tokens
    exists = False
    for t in tokens:
        if t['token'] == token_to_revoke:
            exists = True
            break

    if not exists:
        return jsonify({"error": "Token not found"}), 404

    # Remove token from database and ram
    delete_token(token_to_revoke)
    tokens = [t for t in tokens if t['token'] != token_to_revoke]

    return jsonify({"message": "Token revoked successfully"}), 200



@app.route('/list_tokens', methods=['GET'])
def list_tokens():
    if 'write' not in request.scopes:
        return jsonify({"error": "Insufficient permissions"}), 403

    sanitized_tokens = [
        {"id": i, "scope": t['scope'], "expired_at": t['expired_at'], "token": t['token']} 
        for i, t in enumerate(tokens)
    ]

    return jsonify({"tokens": sanitized_tokens}), 200



@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    if 'infer' not in request.scopes:
        return jsonify({"error": "Insufficient permissions"}), 403

    data = request.get_json()
    response = proxy_request(config['INFER']['completions'], data)

    return Response(
        response=json.dumps(response),
        status=200,
        mimetype='application/json'
    )

# Generic v1 API endpoint handler to capture all v1 routes
@app.route('/v1/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def v1_api(subpath):
    if 'infer' not in request.scopes:
        return jsonify({"error": "Insufficient permissions"}), 403

    data = request.get_json(silent=True) or {}
    target_url = f'{config.get("INFER", {}).get("v1", "http://localhost:1234/v1/")}/{subpath}'
    response = proxy_request(target_url, data, method=request.method)

    return Response(
        response=json.dumps(response),
        status=200,
        mimetype='application/json'
    )

if __name__ == '__main__':
    setup()
    print(json.dumps(tokens))
    app.run(host=config['APP']['host'], port=config['APP']['port'], threaded=True)