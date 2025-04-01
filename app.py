import json
import os
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from anthropic import Anthropic
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

# Load sample data
def load_sample_data():
    try:
        with open(Config.SAMPLE_DATA_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading sample data: {e}")
        return {"patients": []}

# Load schema
def load_schema():
    try:
        with open(Config.SCHEMA_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading schema: {e}")
        return {"schema": {}}

# Prepare context for Claude
def prepare_context():
    # Load data and schema for context
    sample_data = load_sample_data()
    schema = load_schema()
    
    return {
        "schema": schema.get("schema", {}),
        "data": sample_data
    }

# Initialize Anthropic client with minimal parameters
anthropic_client = None
try:
    anthropic_client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
except Exception as e:
    logger.error(f"Failed to initialize Anthropic client: {e}")

@app.route('/ask', methods=['POST'])
def ask_claude():
    # Check if client is initialized
    if not anthropic_client:
        return jsonify({
            "message": "Anthropic client not initialized. Check API key and logs."
        }), 500
    
    try:
        # Get user message
        user_message = request.json.get('message', '')
        
        # Prepare context
        context = prepare_context()
        
        # Prepare system prompt with context
        system_prompt = (
            "You are a veterinary assistant helping to retrieve patient information. "
            "Use the following context to answer questions precisely:\n\n"
            f"Schema: {json.dumps(context['schema'])}\n\n"
            f"Data: {json.dumps(context['data'])}\n\n"
            "Guidelines:\n"
            "- Directly answer questions about patient records\n"
            "- If information is not found, clearly state that\n"
            "- Provide concise and helpful responses"
        )
        
        # Send message to Claude with new API approach
        response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            system=system_prompt,  # Use top-level system parameter
            messages=[
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )
        
        # Return Claude's response
        return jsonify({
            "response": response.content[0].text
        })
    
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return jsonify({
            "message": f"An error occurred: {str(e)}"
        }), 500

# Serve the HTML file
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    # Validate configuration
    Config.validate()
    
    # Run the app
    app.run(
        host=Config.HOST, 
        port=Config.PORT, 
        debug=Config.DEBUG
    )
