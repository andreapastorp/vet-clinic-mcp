import os
import json
import subprocess
import threading
from flask import Flask, request, jsonify, send_from_directory
import asyncio
from flask_cors import CORS
from dotenv import load_dotenv

# Import MCP client functionality
from backend.mcp_client import process_message, get_all_patients, get_patient_details, create_patient

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__, 
    static_folder='dist',
    static_url_path=''
)

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# MCP server process
mcp_server_process = None

def start_mcp_server():
    """Start the MCP server as a subprocess."""
    global mcp_server_process
    # Start the server if not already running
    if mcp_server_process is None or mcp_server_process.poll() is not None:
        print("Starting MCP server...")
        mcp_server_process = subprocess.Popen(
            ["python", "backend/server.py"],  # Update path to your server.py
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("MCP server started")

# Start MCP server when Flask app starts
start_mcp_server()

# API Routes
@app.route('/chat', methods=['POST'])
def chat():
    """Process chat messages through MCP."""
    print("Received chat request")
    data = request.json
    message = data.get('message', '')
    
    # Create a new event loop for async operation
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Call existing MCP client function
        result = loop.run_until_complete(process_message(message))
        return jsonify(result)
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        loop.close()

@app.route('/patients', methods=['GET'])
def get_patients():
    """Get all patients data."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        patients_data = loop.run_until_complete(get_all_patients())
        return jsonify(patients_data)
    finally:
        loop.close()

@app.route('/patients/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Get details for a specific patient."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        patient_data = loop.run_until_complete(get_patient_details(patient_id))
        return jsonify(patient_data)
    finally:
        loop.close()

@app.route('/patients', methods=['POST'])
def create_new_patient():
    """Create a new patient."""
    data = request.json
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(create_patient(data))
        return jsonify({"message": result})
    finally:
        loop.close()

# Serve React app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
