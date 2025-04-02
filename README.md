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

3. Initialize the database:
   ```
   python init.py
   ```

## Running the Server

```
python client.py
```
