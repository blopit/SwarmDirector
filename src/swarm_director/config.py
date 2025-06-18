import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Connection Pool Configuration
    # Base settings - can be overridden in environment-specific configs
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),
        'pool_pre_ping': os.environ.get('DB_POOL_PRE_PING', 'true').lower() in ['true', '1', 'yes'],
        'echo': False  # Will be overridden in development
    }
    
    # Mail configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Application-specific configuration
    AGENTS_PER_PAGE = 20
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    
    @staticmethod
    def init_app(app):
        """Initialize application with this configuration"""
        # Adjust engine options based on database type
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if db_uri.startswith('sqlite://'):
            # SQLite doesn't support connection pooling parameters
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                k: v for k, v in app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {}).items()
                if k not in ['pool_size', 'max_overflow', 'pool_timeout', 'pool_recycle']
            }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(__file__), 'swarm_director_dev.db')
    
    # Development-specific connection pool settings
    # Note: SQLite doesn't support connection pooling, these are for PostgreSQL/MySQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        'pool_size': 5,  # Smaller pool for development
        'max_overflow': 10,
        'pool_timeout': 20,
        'echo': True,  # Enable SQL logging in development
        'pool_pre_ping': True  # Always ping connections to catch issues early
    }
    
    @classmethod
    def init_app(cls, app):
        """Development-specific initialization"""
        Config.init_app(app)

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # Testing-specific connection pool settings
    # Note: SQLite in-memory databases don't support connection pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'echo': False,  # Disable SQL logging in tests
        'pool_pre_ping': False  # Skip pre-ping for in-memory database
    }
    
    @classmethod
    def init_app(cls, app):
        """Testing-specific initialization"""
        Config.init_app(app)

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(__file__), 'swarm_director.db')
    
    # Production-optimized connection pool settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        'pool_size': 15,  # Larger pool for production concurrency
        'max_overflow': 30,
        'pool_timeout': 60,  # Longer timeout for production stability
        'pool_recycle': 1800,  # Recycle connections more frequently (30 minutes)
        'echo': False,
        'pool_pre_ping': True  # Always ping in production to handle connection drops
    }
    
    @classmethod
    def init_app(cls, app):
        """Production-specific initialization"""
        Config.init_app(app)
        
        # Log to stderr in production
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 