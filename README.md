# Llama Server AuthKeys

## Overview

Llama AuthKeys is a lightweight authentication service built with Flask. It provides token management capabilities, including creating, listing, and revoking tokens. The service also proxies requests to an external API while ensuring proper authorization based on token scopes.

## Features

- **Token Management**: Create, list, and revoke tokens.
- **Scope-based Authorization**: Tokens have associated scopes that determine access levels.
- **Request Logging**: Logs all incoming requests for auditing purposes.
- **Proxy Requests**: Forwards requests to an external API with proper authentication.

## Requirements

- Python 3+
- Flask
- [SQLite3](https://www.sqlite.org/download.html)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/NeuralWeights/llama-server-authkeys.git
   cd llama-server-authkeys
   ```

2. Install dependencies:

   ```bash
   pip install flask
   ```

## Configuration

Align the `config.ini` file to your needs if needed.

```ini
[APP]
host=127.0.0.1
port=5001

[DB]
db_name=authwall.db
root_token=root

[INFER]
completions=http://localhost:1234/v1/chat/completions
v1=http://localhost:1234/v1
```

## Running the Application

1. Start the application:

   ```bash
   python app.py
   ```

2. Access the service at `http://localhost:5001`.

## Usage (CURL)

### List Tokens
`curl -X GET http://localhost:5001/list_tokens -H "Content-Type: application/json" -d "{\"token\": \"root\"}"`

### Create Token
`curl -X POST http://localhost:5001/create_token -H "Content-Type: application/json" -d "{\"token\": \"root\", \"scope\": \"infer:write\", \"expired_at\": 1756800000}"`

### Revoke Token
`curl -X POST http://localhost:5001/revoke_token -H "Content-Type: application/json" -d "{\"token\": \"root\", \"token_to_revoke\": \"the_token_to_revoke\"}"`

### Completions API (Default payload)
`curl -X POST http://localhost:5001/v1/chat/completions -H "Content-Type: application/json" -d "{\"token\": \"your_new_token\", \"model\": \"Llama-3.3-70B-instruct\", \"messages\": [{\"role\": \"system\", \"content\": \"You are a helpful assistant\"}, {\"role\": \"user\", \"content\": \"Hello\"}], \"temperature\": 0.7}"`

### Embeddings API (Default payload)
`curl http://127.0.0.1:5001/v1/embeddings -H "Content-Type: application/json" -d "{ \"model\": \"text-embedding-nomic-embed-text-v1.5\", \"input\": \"Some text to embed\", \"token\": \"root\" }"`