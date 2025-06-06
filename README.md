# Veterinary Practice Management System - MCP Server

A demo for a Model Context Protocol (MCP) server for a Veterinary Practice Management System. It allows veterinarians to access and manage patient data through an interface integrated with Claude.

Vibes only, do not try in production.

## Features

- **Patient Management**: Create, update, and search for patient records
- **Appointment Scheduling**: Add and track patient appointments
- **Health Records**: Manage weight records and vaccination history
- **Schema Exposure**: Access database schema information through resources
- **Prompts**: Ready-to-use prompts for generating concise patient summaries

## Getting Started

1. Clone the repo:
   ```
   git clone https://github.com/andreapastorp/mcp-pims-demo.git
   cd mcp-pims-demo
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Configure the environment variables in `.env`:
```
ANTHROPIC_API_KEY={api_key}

# Database settings
DB_PATH=vet_clinic.db

# Flask
FLASK_ENV=development
FLASK_DEBUG=1
```

4. Build the React application
   ```
   cd frontend
   npm install
   npm run build
   ```

5. Initialize the database:
   ```
   python init.py
   ```

## Running the Server

To run the mcp server in the terminal:
```
cd backend
python client.py
```

Alternatively, run the mcp server with the UI:
1. Run npm
```
cd frontend
npm run dev
```
2. Run the app
```
python app.py
```
