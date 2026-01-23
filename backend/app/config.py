import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Production-grade configuration."""
    
    # Flask
    SECRET_KEY = os.environ['FLASK_SECRET_KEY']
    DEBUG = os.getenv('FLASK_ENV', 'production') == 'development'
    
    # CORS
    CORS_ORIGINS = json.loads(os.getenv('CORS_ORIGINS', '["http://localhost:5173"]'))
    
    # Firebase - Load from JSON file (PROPER WAY)
    @property
    def FIREBASE_CONFIG(self):
        """Load Firebase config from JSON file."""
        config_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
        
        if not config_path:
            raise ValueError(
                "FIREBASE_SERVICE_ACCOUNT_PATH environment variable not set. "
                "Set it to the path of your service-account-key.json file."
            )
        
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(
                f"Firebase service account file not found at: {config_path}\n"
                f"Download it from Firebase Console: "
                f"Project Settings → Service Accounts → Generate New Private Key"
            )
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Validate required structure
            if config_data.get('type') != 'service_account':
                raise ValueError(
                    f"Invalid service account file. Expected 'type: service_account', "
                    f"got: {config_data.get('type')}"
                )
            
            required_fields = ['project_id', 'private_key', 'client_email']
            for field in required_fields:
                if field not in config_data or not config_data[field]:
                    raise ValueError(f"Missing required field: {field}")
            
            return config_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in service account file: {e}")
    
    # Optional: Firebase Web API Key (for client SDK)
    FIREBASE_WEB_API_KEY = os.getenv('FIREBASE_WEB_API_KEY', '')
    
    # Security
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Rate Limiting - Disable in development
    RATELIMIT_ENABLED = os.getenv('FLASK_ENV') != 'development'

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    RATELIMIT_ENABLED = False

class ProductionConfig(Config):
    """Production configuration."""
    CORS_ORIGINS = json.loads(os.getenv('CORS_ORIGINS', '[]'))

# Factory function
def get_config(env=None):
    """Get configuration for environment."""
    env = env or os.getenv('FLASK_ENV', 'development')
    
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
    }
    
    config_class = configs.get(env, DevelopmentConfig)
    return config_class()