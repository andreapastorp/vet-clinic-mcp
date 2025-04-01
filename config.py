import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class"""
    # API Keys
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    
    # API URLs
    ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
    ANTHROPIC_API_VERSION = "2023-06-01"
    
    # Server settings
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', '3000'))
    
    # Paths to data files
    SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.json')
    SAMPLE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'sample-data.json')
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        if not cls.ANTHROPIC_API_KEY and not os.environ.get('SKIP_API_CHECK'):
            print("Warning: ANTHROPIC_API_KEY is not set in environment variables.")
            print("MCP with Claude API will not work without an API key.")
            print("Set SKIP_API_CHECK=1 to bypass this check for development.")
