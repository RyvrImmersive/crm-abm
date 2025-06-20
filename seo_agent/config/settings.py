from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    # Application
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Google Ads API
    GOOGLE_ADS_CLIENT_ID: str = os.getenv('GOOGLE_ADS_CLIENT_ID', '')
    GOOGLE_ADS_CLIENT_SECRET: str = os.getenv('GOOGLE_ADS_CLIENT_SECRET', '')
    GOOGLE_ADS_DEVELOPER_TOKEN: str = os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN', '')
    GOOGLE_ADS_REFRESH_TOKEN: str = os.getenv('GOOGLE_ADS_REFRESH_TOKEN', '')
    GOOGLE_ADS_LOGIN_CUSTOMER_ID: str = os.getenv('GOOGLE_ADS_LOGIN_CUSTOMER_ID', '')
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    
    # Langflow
    LANGFLOW_API_KEY: str = os.getenv('LANGFLOW_API_KEY', '')
    LANGFLOW_URL: str = os.getenv('LANGFLOW_URL', 'http://localhost:7860')
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True

settings = Settings()
