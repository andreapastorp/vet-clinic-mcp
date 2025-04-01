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

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)

@app.route('/ask', methods=['POST'])
def ask_claude():
    """Handle queries to Claude using Model Context Protocol"""
    try:
        # Get user message
        user_message = request.json.get('message', '')
        
        # Prepare context
        context = prepare_context()
        
        # Keep system prompt focused on instructions, not data
        system_prompt = (
            "You are a veterinary assistant helping to retrieve patient information. "
            "Provide concise and helpful responses about the patient data."
        )
        
        # Pure MCP implementation with proper document formatting
        response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_message},
                        # Document 1: Patient data
                        {
                            "type": "document", 
                            "title": "patient_data.json",
                            "source": {
                                "type": "text", 
                                "media_type": "text/plain",
                                "data": json.dumps(context["data"])
                            }
                        },
                        # Document 2: Schema
                        {
                            "type": "document", 
                            "title": "schema.json",
                            "source": {
                                "type": "text", 
                                "media_type": "text/plain",
                                "data": json.dumps(context["schema"])
                            }
                        }
                    ]
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
    # Run the app
    app.run(
        host=Config.HOST, 
        port=Config.PORT, 
        debug=Config.DEBUG
    )
